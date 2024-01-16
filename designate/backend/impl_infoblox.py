# Copyright 2015 Infoblox Inc.
# All Rights Reserved.
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


from urllib.parse import urlparse

from oslo_log import log as logging
from oslo_utils import importutils

from designate.backend import base
from designate import exceptions


infoblox_connector = importutils.try_import('infoblox_client.connector')
infoblox_exceptions = importutils.try_import('infoblox_client.exceptions')
infoblox_object_manager = importutils.try_import(
    'infoblox_client.object_manager'
)
infoblox_objects = importutils.try_import('infoblox_client.objects')


LOG = logging.getLogger(__name__)


class InfobloxBackend(base.Backend):
    """Provides a Designate Backend for Infoblox"""

    __backend_status__ = 'untested'
    __plugin_name__ = 'infoblox'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not infoblox_connector:
            raise exceptions.Backend(
                'The infoblox-client library is not available'
            )

        wapi_host = self.options.get('wapi_host')
        wapi_version = self.options.get('wapi_version')
        wapi_url = self.options.get('wapi_url')

        self.multi_project = self.options.get('multi_tenant')
        self.dns_view = self.options.get('dns_view')
        self.network_view = self.options.get('network_view')
        self.ns_group = self.options.get('ns_group')

        if not wapi_host and wapi_url:
            wapi_host, wapi_version = self.parse_wapi_url(wapi_url)

        options = {
            'host': wapi_host,
            'username': self.options.get('username'),
            'password': self.options.get('password'),
            'http_pool_connections': self.options.get('http_pool_connections'),
            'http_pool_maxsize': self.options.get('http_pool_maxsize'),
            'wapi_version': wapi_version,
            'ssl_verify': self.options.get('sslverify'),
            'cert': self.options.get('cert'),
            'key': self.options.get('key'),
        }
        self.connection = infoblox_connector.Connector(options)
        self.infoblox = infoblox_object_manager.InfobloxObjectManager(
            self.connection
        )

        for master in self.masters:
            if master.port != 53:
                raise exceptions.ConfigurationError(
                    'Infoblox only supports mDNS instances on port 53'
                )

    def create_zone(self, context, zone):
        LOG.info('Create Zone %r', zone)

        dns_zone = zone['name'][0:-1]
        dns_view = self.dns_view
        project_id = context.project_id or zone.tenant_id

        if dns_zone.endswith('in-addr.arpa'):
            zone_format = 'IPV4'
        elif dns_zone.endswith('ip6.arpa'):
            zone_format = 'IPV6'
        else:
            zone_format = 'FORWARD'

        try:
            if self.is_multi_project:
                net_view = self.get_or_create_network_view(project_id)
                dns_view = self.get_or_create_dns_view(net_view)

            if not dns_view:
                raise exceptions.Backend(
                    'Unable to create zone. No DNS View found.'
                )

            self.infoblox.create_dns_zone(
                dns_zone=dns_zone,
                dns_view=dns_view,
                zone_format=zone_format,
                ns_group=self.ns_group,
            )
            self.restart_if_needed()
        except infoblox_exceptions.InfobloxException as e:
            raise exceptions.Backend(e)

    def delete_zone(self, context, zone, zone_params=None):
        LOG.info('Delete Zone %r', zone)

        dns_zone_fqdn = zone['name'][0:-1]
        dns_view = self.dns_view
        project_id = context.project_id or zone.tenant_id

        try:
            if self.is_multi_project:
                net_view = self.get_network_view(project_id)
                dns_view = self.get_or_create_dns_view(
                    net_view, create_if_missing=False
                )

            if not dns_view:
                raise exceptions.Backend(
                    'Unable to delete zone. No DNS View found.'
                )

            self.infoblox.delete_dns_zone(dns_view, dns_zone_fqdn)
            self.restart_if_needed()
        except infoblox_exceptions.InfobloxException as e:
            raise exceptions.Backend(e)

    @staticmethod
    def parse_wapi_url(wapi_url):
        url = urlparse(wapi_url)
        host = url.netloc
        wapi_version = None
        for path in url.path.split('/'):
            if path.startswith('v'):
                wapi_version = path.strip('v')
                break
        return host, wapi_version

    def get_network_view(self, project_id):
        network_views = self.connection.get_object(
            'networkview',
            return_fields=['name'],
            extattrs={'TenantID': {'value': project_id}}
        )
        network_view = None
        if network_views:
            network_view = network_views[0]['name']
        return network_view

    def get_or_create_network_view(self, project_id):
        network_view = self.get_network_view(project_id)
        if not network_view:
            network_view = self.infoblox.create_network_view(
                f'{self.network_view}.{project_id}',
                extattrs={'TenantID': {'value': project_id}}
            ).name
        return network_view

    def get_or_create_dns_view(self, net_view, create_if_missing=True):
        if not net_view:
            return None
        dns_view_name = f'{self.dns_view}.{net_view}'
        dns_view = infoblox_objects.DNSView.search(
            self.connection, name=dns_view_name, return_fields=['name'],
        )
        if not dns_view and create_if_missing:
            dns_view = self.infoblox.create_dns_view(
                self.network_view, dns_view_name
            )
        if not dns_view:
            return None
        return dns_view.name

    @property
    def is_multi_project(self):
        if not self.multi_project or self.multi_project == '0':
            return False
        return True

    def restart_if_needed(self):
        try:
            grid = infoblox_objects.Grid(self.connection)
            grid.fetch(only_ref=True)
            self.connection.call_func(
                'restartservices', grid._ref,
                {
                    'restart_option': 'RESTART_IF_NEEDED',
                    'mode': 'GROUPED',
                    'services': ['DNS'],
                }
            )
        except infoblox_exceptions.InfobloxException:
            LOG.warning('Unable to restart the infoblox dns service.')
