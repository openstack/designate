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
from designateclient.v2 import client
from designateclient import exceptions
from keystoneauth1.identity import v2 as v2_auth
from keystoneauth1.identity import v3 as v3_auth
from keystoneauth1 import session as ks_session
from oslo_log import log as logging

from designate.backend import base
from designate.i18n import _LI
from designate.i18n import _LW


LOG = logging.getLogger(__name__)
CFG_GROUP = 'backend:designate'


class DesignateBackend(base.Backend):
    """
    Support for Designate to Designate using Secondary zones.
    """
    __plugin_name__ = 'designate'
    __backend_status__ = 'release-compatible'

    def __init__(self, target):
        super(DesignateBackend, self).__init__(target)

        self.auth_url = self.options.get('auth_url')
        self.username = self.options.get('username')
        self.password = self.options.get('password')

        # ks v2
        self.tenant_name = self.options.get('tenant_name')
        self.tenant_id = self.options.get('tenant_id')

        # ks v3
        self.project_name = self.options.get('project_name')
        self.project_domain_name = self.options.get(
            'project_domain_name', 'default')
        self.user_domain_name = self.options.get('user_domain_name', 'default')
        self.service_type = self.options.get('service_type', 'dns')

    @property
    def client(self):
        return self._get_client()

    def _get_client(self):
        if self._client is not None:
            return self._client

        if (self.tenant_id is not None or self.tenant_name is not None):
            auth = v2_auth.Password(
                auth_url=self.auth_url,
                username=self.username,
                password=self.password,
                tenant_id=self.tenant_id,
                tenant_name=self.tenant_name)
        elif self.project_name is not None:
            auth = v3_auth.Password(
                auth_url=self.auth_url,
                username=self.username,
                password=self.password,
                project_name=self.project_name,
                project_domain_name=self.project_domain_name,
                user_domain_name=self.user_domain_name)
        else:
            auth = None

        session = ks_session.Session(auth=auth)
        self._client = client.Client(
            session=session, service_type=self.service_type)
        return self._client

    def create_zone(self, context, zone):
        msg = _LI('Creating zone %(d_id)s / %(d_name)s')
        LOG.info(msg, {'d_id': zone['id'], 'd_name': zone['name']})

        masters = ["%s:%s" % (i.host, i.port) for i in self.masters]
        self.client.zones.create(
            zone.name, 'SECONDARY', masters=masters)

    def delete_zone(self, context, zone):
        msg = _LI('Deleting zone %(d_id)s / %(d_name)s')
        LOG.info(msg, {'d_id': zone['id'], 'd_name': zone['name']})

        try:
            self.client.zones.delete(zone.name)
        except exceptions.NotFound:
            msg = _LW("Zone %s not found on remote Designate, Ignoring")
            LOG.warning(msg, zone.id)
