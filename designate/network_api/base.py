# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
import eventlet.patcher
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate.plugin import DriverPlugin


LOG = logging.getLogger(__name__)
# NOTE(kiall): This is a workaround for bug #1424621, a broken reimplementation
#              of eventlet's 0.17.0 monkey patching of dnspython.
reversename = eventlet.patcher.original('dns.reversename')


class NetworkAPI(DriverPlugin):
    """
    Base API
    """
    __plugin_ns__ = 'designate.network_api'
    __plugin_type__ = 'network_api'

    def _endpoints(self, service_catalog=None, service_type=None,
                   endpoint_type='publicURL', config_section=None,
                   region=None):
        if service_catalog is not None and len(service_catalog):
            endpoints = self._endpoints_from_catalog(
                service_catalog, service_type, endpoint_type,
                region=region)
        elif config_section is not None:
            endpoints = []
            for u in cfg.CONF[config_section].endpoints:
                e_region, e = u.split('|')
                # Filter if region is given
                if (e_region and region) and e_region != region:
                    continue
                endpoints.append((e, e_region))

            if not endpoints:
                msg = 'Endpoints are not configured'
                raise exceptions.ConfigurationError(msg)
        else:
            msg = 'No service_catalog and no configured endpoints'
            raise exceptions.ConfigurationError(msg)

        LOG.debug('Returning endpoints: %s', endpoints)
        return endpoints

    def _endpoints_from_catalog(self, service_catalog, service_type,
                                endpoint_type, region=None):
        """
        Return the endpoints for the given service from the context's sc
        or lookup towards the configured keystone.

        return [('http://endpoint', 'region')]
        """
        urls = []
        for svc in service_catalog:
            if svc['type'] != service_type:
                continue
            for url in svc['endpoints']:
                if endpoint_type in url:
                    if region is not None and url['region'] != region:
                        continue
                    urls.append((url[endpoint_type], url['region']))
        if not urls:
            raise exceptions.NetworkEndpointNotFound
        return urls

    def list_floatingips(self, context, region=None):
        """
        List Floating IPs.

        Should return something like:

        [{
            'address': '<ip address'>,
            'region': '<region where this belongs>',
            'id': '<id of the FIP>'
        }]
        """
        raise NotImplementedError

    @staticmethod
    def address_zone(address):
        """
        Get the zone a address belongs to.
        """
        parts = reversed(address.split('.')[:-1])
        return '%s.in-addr.arpa.' % ".".join(parts)

    @staticmethod
    def address_name(address):
        """
        Get the name for the address
        """
        return reversename.from_address(address).to_text().decode('utf-8')
