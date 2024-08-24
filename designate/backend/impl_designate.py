# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
import ipaddress

from designateclient import exceptions
from designateclient.v2 import client
from keystoneauth1.identity import v3 as v3_auth
from keystoneauth1 import session as ks_session
from oslo_log import log as logging

from designate.backend import base


LOG = logging.getLogger(__name__)
CFG_GROUP_NAME = 'backend:designate'


class DesignateBackend(base.Backend):
    """
    Support for Designate to Designate using Secondary zones.
    """
    __plugin_name__ = 'designate'
    __backend_status__ = 'untested'

    def __init__(self, target):
        super().__init__(target)

        self.auth_url = self.options.get('auth_url')
        self.username = self.options.get('username')
        self.password = self.options.get('password')

        self.project_name = self.options.get('project_name')
        self.project_domain_name = self.options.get(
            'project_domain_name', 'default')
        self.user_domain_name = self.options.get('user_domain_name', 'default')
        self.service_type = self.options.get('service_type', 'dns')
        self.region_name = self.options.get('region_name')

    @property
    def client(self):
        return self._get_client()

    def _get_client(self):
        if self._client is not None:
            return self._client

        auth = v3_auth.Password(
            auth_url=self.auth_url,
            username=self.username,
            password=self.password,
            project_name=self.project_name,
            project_domain_name=self.project_domain_name,
            user_domain_name=self.user_domain_name,
        )

        session = ks_session.Session(auth=auth)
        self._client = client.Client(
            session=session,
            service_type=self.service_type,
            region_name=self.region_name,
        )
        return self._client

    def create_zone(self, context, zone):
        LOG.info('Creating zone %(d_id)s / %(d_name)s',
                 {'d_id': zone['id'], 'd_name': zone['name']})

        masters = []
        for master in self.masters:
            host = master.host
            try:
                if ipaddress.ip_address(host).version == 6:
                    host = '[%s]' % host
            except ValueError:
                pass
            masters.append('%s:%d' % (host, master.port))

        self.client.zones.create(
            zone.name, 'SECONDARY', masters=masters)

    def delete_zone(self, context, zone, zone_params=None):
        LOG.info('Deleting zone %(d_id)s / %(d_name)s',
                 {'d_id': zone['id'], 'd_name': zone['name']})

        try:
            self.client.zones.delete(zone.name)
        except exceptions.NotFound:
            LOG.warning("Zone %s not found on remote Designate, Ignoring",
                        zone.id)
