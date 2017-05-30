# Copyright 2012-2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from oslo_utils import importutils

from designate import exceptions
from designate import utils
from designate.backend import base


try:
    SudsClient = importutils.import_class("suds.client.Client")
    HttpAuthenticated = importutils.import_class(
        "suds.transport.https.HttpAuthenticated")

except ImportError:
    SudsClient = None

    class HttpAuthenticated(object):
        pass


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


class DuplicateZone(exceptions.DuplicateZone, EnhancedDNSException):
    """
    Raised when an attempt to create a zone which is registered to another
    Akamai account is made
    """
    pass


class Forbidden(exceptions.Forbidden, EnhancedDNSException):
    """
    Raised when an attempt to modify a zone which is registered to another
    Akamai account is made.

    This appears to be returned when creating a new subzone of zone which
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
        # Ensure Suds (or suds-jerko) have been installed
        if SudsClient is None:
            raise EnhancedDNSException(
                "Dependency missing, please install suds or suds-jurko")

        # Prepare a SUDS transport with the appropriate credentials
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

    def getZone(self, zoneName):
        LOG.debug("Performing getZone with zoneName: %s" % zoneName)
        zoneName = self._sanitizeZoneName(zoneName)

        try:
            return self.client.service.getZone(zoneName=zoneName)
        except Exception as e:
            raise EnhancedDNSException('Akamai Communication Failure: %s' % e)

    def setZones(self, zones):
        LOG.debug("Performing setZones")
        try:
            return self.client.service.setZones(zones=zones)
        except Exception as e:
            if 'You do not have permission to view this zone' in str(e):
                raise DuplicateZone()
            elif 'You do not have access to edit this zone' in str(e):
                raise Forbidden()
            elif 'basic auth failed' in str(e):
                raise exceptions.ConfigurationError(
                    'Invalid Akamai credentials')
            else:
                raise EnhancedDNSException('Akamai Communication Failure: %s'
                                           % e)

    def setZone(self, zone):
        LOG.debug("Performing setZone with zoneName: %s" % zone.zoneName)
        try:
            self.client.service.setZone(zone=zone)
        except Exception as e:
            if 'You do not have permission to view this zone' in str(e):
                raise DuplicateZone()
            elif 'You do not have access to edit this zone' in str(e):
                raise Forbidden()
            elif 'basic auth failed' in str(e):
                raise exceptions.ConfigurationError(
                    'Invalid Akamai credentials')
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
            # *READ THIS SECTION BEFORE MAKING ANY CHANGES*
            # Added 01/2017 by Graham Hayes.
            # If you have run a spell checking tool against the repo, and it
            # changes the line below - the patch will get -2'd.
            # This is matching a string that comes back from the akamai API.
            # If the akamai API changes - then this should change, but no
            # other reason.
            if 'Could not retrive object ID for zone' in str(e):
                # The zone has already been purged, ignore and move on
                pass
            elif 'The following zones are still delegated to Akamai' in str(e):
                raise DelegationExists()
            elif 'basic auth failed' in str(e):
                raise exceptions.ConfigurationError(
                    'Invalid Akamai credentials')
            else:
                raise EnhancedDNSException('Akamai Communication Failure: %s'
                                           % e)

    def _sanitizeZoneName(self, zoneName):
        return zoneName.rstrip('.').lower()


def build_zone(client, target, zone):
    masters = [m.host for m in target.masters]

    if target.options.get("tsig_key_name", None):
        return client.buildZone(
            zone.name,
            masters,
            zone.id,
            target.options.get("tsig_key_name", None),
            target.options.get("tsig_key_secret", None),
            target.options.get("tsig_key_algorithm", None))
    else:
        return client.buildZone(
            zone.name,
            masters,
            zone.id)


class AkamaiBackend(base.Backend):
    __plugin_name__ = 'akamai'

    __backend_status__ = 'release-compatible'

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

        self.client = EnhancedDNSClient(self.username, self.password)

        for m in self.masters:
            if m.port != 53:
                raise exceptions.ConfigurationError(
                    "Akamai only supports mDNS instances on port 53")

    def create_zone(self, context, zone):
        """Create a DNS zone"""
        zone = build_zone(self.client, self.target, zone)

        self.client.setZone(zone=zone)

    def delete_zone(self, context, zone):
        """Delete a DNS zone"""
        self.client.deleteZone(zoneName=zone['name'])
