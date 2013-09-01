# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.openstack.common.rpc import proxy as rpc_proxy

LOG = logging.getLogger(__name__)


class CentralAPI(rpc_proxy.RpcProxy):
    """
    Client side of the central RPC API.

    API version history:

        1.0 - Initial version
        1.1 - Add new finder methods
        1.2 - Add get_tenant and get_tenants
        1.3 - Add get_absolute_limits
        2.0 - Renamed most get_resources to find_resources
        2.1 - Add quota methods

    """
    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.central_topic
        super(CentralAPI, self).__init__(topic=topic, default_version='2.0')

    # Misc Methods
    def get_absolute_limits(self, context):
        LOG.info("get_absolute_limits: Calling central's get_absolute_limits.")
        msg = self.make_msg('get_absolute_limits')

        return self.call(context, msg)

    # Quota Methods
    def get_quotas(self, context, tenant_id):
        LOG.info("get_quotas: Calling central's get_quotas.")
        msg = self.make_msg('get_quotas', tenant_id=tenant_id)

        return self.call(context, msg, version='2.1')

    def get_quota(self, context, tenant_id, resource):
        LOG.info("get_quota: Calling central's get_quota.")
        msg = self.make_msg('get_quota', tenant_id=tenant_id,
                            resource=resource)

        return self.call(context, msg, version='2.1')

    def set_quota(self, context, tenant_id, resource, hard_limit):
        LOG.info("set_quota: Calling central's set_quota.")
        msg = self.make_msg('set_quota', tenant_id=tenant_id,
                            resource=resource, hard_limit=hard_limit)

        return self.call(context, msg, version='2.1')

    def reset_quotas(self, context, tenant_id):
        LOG.info("reset_quotas: Calling central's reset_quotas.")
        msg = self.make_msg('reset_quotas', tenant_id=tenant_id)

        return self.call(context, msg, version='2.1')

    # Server Methods
    def create_server(self, context, values):
        LOG.info("create_server: Calling central's create_server.")
        msg = self.make_msg('create_server', values=values)

        return self.call(context, msg)

    def find_servers(self, context, criterion=None):
        LOG.info("find_servers: Calling central's find_servers.")
        msg = self.make_msg('find_servers', criterion=criterion)

        return self.call(context, msg)

    def get_server(self, context, server_id):
        LOG.info("get_server: Calling central's get_server.")
        msg = self.make_msg('get_server', server_id=server_id)

        return self.call(context, msg)

    def update_server(self, context, server_id, values):
        LOG.info("update_server: Calling central's update_server.")
        msg = self.make_msg('update_server', server_id=server_id,
                            values=values)

        return self.call(context, msg)

    def delete_server(self, context, server_id):
        LOG.info("delete_server: Calling central's delete_server.")
        msg = self.make_msg('delete_server', server_id=server_id)

        return self.call(context, msg)

    # TSIG Key Methods
    def create_tsigkey(self, context, values):
        LOG.info("create_tsigkey: Calling central's create_tsigkey.")
        msg = self.make_msg('create_tsigkey', values=values)

        return self.call(context, msg)

    def find_tsigkeys(self, context, criterion=None):
        LOG.info("find_tsigkeys: Calling central's find_tsigkeys.")
        msg = self.make_msg('find_tsigkeys', criterion=criterion)

        return self.call(context, msg)

    def get_tsigkey(self, context, tsigkey_id):
        LOG.info("get_tsigkey: Calling central's get_tsigkey.")
        msg = self.make_msg('get_tsigkey', tsigkey_id=tsigkey_id)

        return self.call(context, msg)

    def update_tsigkey(self, context, tsigkey_id, values):
        LOG.info("update_tsigkey: Calling central's update_tsigkey.")
        msg = self.make_msg('update_tsigkey', tsigkey_id=tsigkey_id,
                            values=values)

        return self.call(context, msg)

    def delete_tsigkey(self, context, tsigkey_id):
        LOG.info("delete_tsigkey: Calling central's delete_tsigkey.")
        msg = self.make_msg('delete_tsigkey', tsigkey_id=tsigkey_id)

        return self.call(context, msg)

    # Tenant Methods
    def find_tenants(self, context):
        LOG.info("find_tenants: Calling central's find_tenants.")
        msg = self.make_msg('find_tenants')

        return self.call(context, msg)

    def get_tenant(self, context, tenant_id):
        LOG.info("get_tenant: Calling central's get_tenant.")
        msg = self.make_msg('get_tenant', tenant_id=tenant_id)

        return self.call(context, msg)

    def count_tenants(self, context):
        LOG.info("count_tenants: Calling central's count_tenants.")
        msg = self.make_msg('count_tenants')

        return self.call(context, msg)

    # Domain Methods
    def create_domain(self, context, values):
        LOG.info("create_domain: Calling central's create_domain.")
        msg = self.make_msg('create_domain', values=values)

        return self.call(context, msg)

    def get_domain(self, context, domain_id):
        LOG.info("get_domain: Calling central's get_domain.")
        msg = self.make_msg('get_domain', domain_id=domain_id)

        return self.call(context, msg)

    def get_domain_servers(self, context, domain_id):
        LOG.info("get_domain_servers: Calling central's get_domain_servers.")
        msg = self.make_msg('get_domain_servers', domain_id=domain_id)

        return self.call(context, msg)

    def find_domains(self, context, criterion=None):
        LOG.info("find_domains: Calling central's find_domains.")
        msg = self.make_msg('find_domains', criterion=criterion)

        return self.call(context, msg)

    def find_domain(self, context, criterion):
        LOG.info("find_domain: Calling central's find_domain.")
        msg = self.make_msg('find_domain', criterion=criterion)

        return self.call(context, msg)

    def update_domain(self, context, domain_id, values, increment_serial=True):
        LOG.info("update_domain: Calling central's update_domain.")
        msg = self.make_msg('update_domain',
                            domain_id=domain_id,
                            values=values,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    def delete_domain(self, context, domain_id):
        LOG.info("delete_domain: Calling central's delete_domain.")
        msg = self.make_msg('delete_domain', domain_id=domain_id)

        return self.call(context, msg)

    def count_domains(self, context, criterion=None):
        LOG.info("count_domains: Calling central's count_domains.")
        msg = self.make_msg('count_domains', criterion=criterion)

        return self.call(context, msg)

    def touch_domain(self, context, domain_id):
        LOG.info("touch_domain: Calling central's touch_domain.")
        msg = self.make_msg('touch_domain', domain_id=domain_id)

        return self.call(context, msg)

    # Record Methods
    def create_record(self, context, domain_id, values, increment_serial=True):
        LOG.info("create_record: Calling central's create_record.")
        msg = self.make_msg('create_record',
                            domain_id=domain_id,
                            values=values,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    def get_record(self, context, domain_id, record_id):
        LOG.info("get_record: Calling central's get_record.")
        msg = self.make_msg('get_record',
                            domain_id=domain_id,
                            record_id=record_id)

        return self.call(context, msg)

    def find_records(self, context, domain_id, criterion=None):
        LOG.info("find_records: Calling central's find_records.")
        msg = self.make_msg('find_records',
                            domain_id=domain_id,
                            criterion=criterion)

        return self.call(context, msg)

    def find_record(self, context, domain_id, criterion=None):
        LOG.info("find_record: Calling central's find_record.")
        msg = self.make_msg('find_record',
                            domain_id=domain_id,
                            criterion=criterion)

        return self.call(context, msg)

    def update_record(self, context, domain_id, record_id, values,
                      increment_serial=True):
        LOG.info("update_record: Calling central's update_record.")
        msg = self.make_msg('update_record',
                            domain_id=domain_id,
                            record_id=record_id,
                            values=values,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    def delete_record(self, context, domain_id, record_id,
                      increment_serial=True):
        LOG.info("delete_record: Calling central's delete_record.")
        msg = self.make_msg('delete_record',
                            domain_id=domain_id,
                            record_id=record_id,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    def count_records(self, context, criterion=None):
        LOG.info("count_records: Calling central's count_records.")
        msg = self.make_msg('count_records', criterion=criterion)

        return self.call(context, msg)

    # Sync Methods
    def sync_domains(self, context):
        LOG.info("sync_domains: Calling central's sync_domains.")
        msg = self.make_msg('sync_domains')

        return self.call(context, msg)

    def sync_domain(self, context, domain_id):
        LOG.info("sync_domain: Calling central's sync_domains.")
        msg = self.make_msg('sync_domain', domain_id=domain_id)

        return self.call(context, msg)

    def sync_record(self, context, domain_id, record_id):
        LOG.info("sync_record: Calling central's sync_record.")
        msg = self.make_msg('sync_record',
                            domain_id=domain_id,
                            record_id=record_id)

        return self.call(context, msg)
