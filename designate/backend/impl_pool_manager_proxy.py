# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
from designate.openstack.common import log as logging
from designate.backend import base
from designate.pool_manager import rpcapi as pool_manager_rpcapi


LOG = logging.getLogger(__name__)

POOL_MANAGER_API = None


def get_pool_manager_api():
    """
    The rpc.get_client() which is called upon the API object initialization
    will cause a assertion error if the designate.rpc.TRANSPORT isn't setup by
    rpc.init() before.

    This fixes that by creating the rpcapi when demanded.
    """
    global POOL_MANAGER_API
    if not POOL_MANAGER_API:
        POOL_MANAGER_API = pool_manager_rpcapi.PoolManagerAPI()
    return POOL_MANAGER_API


class PoolManagerProxyBackend(base.Backend):
    __plugin_name__ = 'pool_manager_proxy'

    def __init__(self, *args, **kwargs):
        super(PoolManagerProxyBackend, self).__init__(*args, **kwargs)
        self.pool_manager = get_pool_manager_api()

    def create_server(self, context, server):
        LOG.debug('Create Server')
        domains = self.central_service.find_domains(self.admin_context)
        for domain in domains:
            self.pool_manager.update_domain(context, domain)

    def update_server(self, context, server):
        LOG.debug('Update Server')
        domains = self.central_service.find_domains(self.admin_context)
        for domain in domains:
            self.pool_manager.update_domain(context, domain)

    def delete_server(self, context, server):
        LOG.debug('Delete Server')
        domains = self.central_service.find_domains(self.admin_context)
        for domain in domains:
            self.pool_manager.update_domain(context, domain)

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')
        self.pool_manager.create_domain(context, domain)

    def update_domain(self, context, domain):
        LOG.debug('Update Domain')
        self.pool_manager.update_domain(context, domain)

    def delete_domain(self, context, domain):
        LOG.debug('Delete Domain')
        self.pool_manager.delete_domain(context, domain)

    def create_recordset(self, context, domain, recordset):
        LOG.debug('Create RecordSet')
        self.pool_manager.update_domain(context, domain)

    def update_recordset(self, context, domain, recordset):
        LOG.debug('Update RecordSet')
        self.pool_manager.update_domain(context, domain)

    def delete_recordset(self, context, domain, recordset):
        LOG.debug('Delete RecordSet')
        self.pool_manager.update_domain(context, domain)

    def create_record(self, context, domain, recordset, record):
        LOG.debug('Create Record')
        self.pool_manager.update_domain(context, domain)

    def update_record(self, context, domain, recordset, record):
        LOG.debug('Update Record')
        self.pool_manager.update_domain(context, domain)

    def delete_record(self, context, domain, recordset, record):
        LOG.debug('Delete Record')
        self.pool_manager.update_domain(context, domain)
