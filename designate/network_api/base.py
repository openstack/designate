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
from oslo_log import log as logging

import designate.conf
from designate import exceptions
from designate.plugin import DriverPlugin


CONF = designate.conf.CONF
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
        configured_endpoints = self.get_configured_endpoints(config_section)
        if configured_endpoints:
            endpoints = self.endpoints_from_config(
                configured_endpoints,
                region=region,
            )
        elif service_catalog:
            endpoints = self.endpoints_from_catalog(
                service_catalog, service_type, endpoint_type,
                region=region,
            )
        else:
            raise exceptions.ConfigurationError(
                'No service_catalog and no configured endpoints'
            )

        LOG.debug('Returning endpoints: %s', endpoints)
        return endpoints

    @staticmethod
    def endpoints_from_config(configured_endpoints, region=None):
        """
        Return the endpoints for the given service from the configuration.

        return [('http://endpoint', 'region')]
        """
        endpoints = []
        for endpoint_data in configured_endpoints:
            if not endpoint_data:
                continue
            endpoint_region, endpoint = endpoint_data.split('|')
            if region and endpoint_region != region:
                continue
            endpoints.append((endpoint, endpoint_region))
        if not endpoints:
            raise exceptions.ConfigurationError(
                'Endpoints are not correctly configured'
            )
        return endpoints

    @staticmethod
    def endpoints_from_catalog(service_catalog, service_type, endpoint_type,
                               region=None):
        """
        Return the endpoints for the given service from the context's sc
        or lookup towards the configured keystone.

        return [('http://endpoint', 'region')]
        """
        endpoints = []
        for svc in service_catalog:
            if svc['type'] != service_type:
                continue
            for endpoint_data in svc['endpoints']:
                if endpoint_type not in endpoint_data:
                    continue
                endpoint = endpoint_data[endpoint_type]
                endpoint_region = endpoint_data['region']
                if region and endpoint_region != region:
                    continue
                endpoints.append((endpoint, endpoint_region))
        if not endpoints:
            raise exceptions.NetworkEndpointNotFound()
        return endpoints

    @staticmethod
    def get_configured_endpoints(config_section):
        """
        Returns endpoints from a specific section in the configuration.

        return ['region|http://endpoint']
        """
        if not config_section:
            return None
        cfg_group = CONF[config_section]
        return cfg_group.endpoints

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
        name = reversename.from_address(address).to_text()
        return name
