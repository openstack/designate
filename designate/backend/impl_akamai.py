# Copyright 2012-2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import os

from oslo_log import log as logging
from oslo_config import cfg
from suds.client import Client as SudsClient
from suds.transport.https import HttpAuthenticated

from designate import exceptions
from designate import utils
from designate.backend import base


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

WSDL = os.path.join(os.path.dirname(__file__),
                    '..',
                    'resources',
                    'wsdl',
                    'EnhancedDNS.xml')


class EnhancedDNSException(exceptions.Backend):
    pass


class DelegationExists(exceptions.BadRequest, EnhancedDNSException):
    """
    Raised when an attempt to delete a zone which is still delegated to Akamai
    is made
    """
    error_type = 'delegation_exists'


class DuplicateDomain(exceptions.DuplicateDomain, EnhancedDNSException):
    """
    Raised when an attempt to create a zone which is registered to another
    Akamai account is made
    """
    pass


class Forbidden(exceptions.Forbidden, EnhancedDNSException):
    """
    Raised when an attempt to modify a zone which is registered to another
    Akamai account is made.

    This appears to be returned when creating a new subdomain of domain which
    already exists in another Akamai account.
    """
    pass


class EnhancedDNSHttpAuthenticated(HttpAuthenticated):
    def addenhanceddnsheaders(self, request):
        request.headers['Pragma'] = ('akamai-x-get-request-id, '
                                     'akamai-x-cache-on, '
                                     'akamai-x-cache-remote-on, '
                                     'akamai-x-get-cache-key')

    def logenhanceddnsheaders(self, response):
        request_id = response.headers.get('x-akamai-request-id', '-')
        cache = response.headers.get('x-cache', '-')
        cache_key = response.headers.get('x-cache-key', '-')
        cache_remote = response.headers.get('x-cache-remote', '-')

        LOG.debug('Akamai Request-ID: %s, Cache-Key: %s, Cache: %s, '
                  'Cache-Remote: %s', request_id, cache_key, cache,
                  cache_remote)

    def send(self, request):
        self.addenhanceddnsheaders(request)

        response = HttpAuthenticated.send(self, request)

        self.logenhanceddnsheaders(response)

        return response


class EnhancedDNSClient(object):
    """EnhancedDNS SOAP API Client"""

    def __init__(self, username, password):
        # Prepare a SUDS transport with the approperiate credentials
        transport = EnhancedDNSHttpAuthenticated(
            username=username,
            password=password,
            proxy=utils.get_proxies())

        # Prepare a SUDS client
        self.client = SudsClient(CONF['backend:akamai'].enhanceddns_wsdl,
                                 transport=transport)

    def buildZone(self, zoneName, masters, endCustomerId, tsigKeyName=None,
                  tsigKey=None, tsigAlgorithm=None):
        zone = self.client.factory.create('ns3:Zone')

        # Set some defaults
        zone.transferMode = "axfr"
        zone.type = "edns"
        zone.notify = 1
        zone.dnssec = False

        # Set the remaining options
        zone.zoneName = self._sanitizeZoneName(zoneName)
        zone.masters = masters
        zone.tsigKeyName = tsigKeyName
        zone.tsigKey = tsigKey
        zone.tsigAlgorithm = tsigAlgorithm
        zone.endCustomerId = endCustomerId

        return zone

    def setZone(self, zone):
        LOG.debug("Performing setZone with zoneName: %s", zone.zoneName)
        try:
            self.client.service.setZone(zone=zone)
        except Exception as e:
            if 'You do not have permission to view this zone' in str(e):
                raise DuplicateDomain()
            elif 'You do not have access to edit this zone' in str(e):
                raise Forbidden()
            else:
                raise EnhancedDNSException('Akamai Communication Failure: %s'
                                           % e)

    def deleteZone(self, zoneName):
        LOG.debug("Performing deleteZone with zoneName: %s", zoneName)
        zoneName = self._sanitizeZoneName(zoneName)

        self.deleteZones(zoneNames=[zoneName])

    def deleteZones(self, zoneNames):
        LOG.debug("Performing deleteZones with zoneNames: %r", zoneNames)
        zoneNames = [self._sanitizeZoneName(zN) for zN in zoneNames]

        try:
            self.client.service.deleteZones(zoneNames=zoneNames)
        except Exception as e:
            if 'Could not retrive object ID for zone' in str(e):
                # The zone has already been purged, ignore and move on
                pass
            elif 'The following zones are still delegated to Akamai' in str(e):
                raise DelegationExists()
            else:
                raise EnhancedDNSException('Akamai Communication Failure: %s'
                                           % e)

    def _sanitizeZoneName(self, zoneName):
        return zoneName.rstrip('.').lower()


class AkamaiBackend(base.Backend):
    __plugin_name__ = 'akamai'

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(
            name='backend:akamai', title='Backend options for Akamai'
        )

        opts = [
            cfg.StrOpt('enhanceddns_wsdl',
               default='file://%s' % WSDL,
               help='Akamai EnhancedDNS WSDL URL'),
        ]

        return [(group, opts)]

    def __init__(self, target):
        super(AkamaiBackend, self).__init__(target)

        self.username = self.options.get('username')
        self.password = self.options.get('password')

        self.tsig_key_name = self.options.get('tsig_key_name', None)
        self.tsig_key_algorithm = self.options.get('tsig_key_algorithm', None)
        self.tsig_key_secret = self.options.get('tsig_key_secret', None)

        self.client = EnhancedDNSClient(self.username, self.password)

    def _build_zone(self, domain):
        masters = ["%(host)s:%(port)d" % m for m in self.masters]

        if self.tsig_key_name is not None:
            return self.client.buildZone(
                domain.name,
                masters,
                domain.id,
                self.tsig_key_name,
                self.tsig_key_secret,
                self.tsig_key_algorithm)

        else:
            return self.client.buildZone(
                domain.name,
                masters,
                domain.id)

    def create_domain(self, context, domain):
        """Create a DNS domain"""
        zone = self._build_zone(domain)

        self.client.setZone(zone=zone)

    def delete_domain(self, context, domain):
        """Delete a DNS domain"""
        self.client.deleteZone(zoneName=domain['name'])
