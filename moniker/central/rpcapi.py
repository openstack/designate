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
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common.rpc import proxy as rpc_proxy

LOG = logging.getLogger(__name__)


class CentralAPI(rpc_proxy.RpcProxy):
    """
    Client side of the central RPC API.

    API version history:

        1.0 - Initial version
    """
    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.central_topic
        super(CentralAPI, self).__init__(topic=topic, default_version='1.0')

    # Server Methods
    def create_server(self, context, values):
        msg = self.make_msg('create_server', values=values)

        return self.call(context, msg)

    def get_servers(self, context, criterion=None):
        msg = self.make_msg('get_servers', criterion=criterion)

        return self.call(context, msg)

    def get_server(self, context, server_id):
        msg = self.make_msg('get_server', server_id=server_id)

        return self.call(context, msg)

    def update_server(self, context, server_id, values):
        msg = self.make_msg('update_server', server_id=server_id,
                            values=values)

        return self.call(context, msg)

    def delete_server(self, context, server_id):
        msg = self.make_msg('delete_server', server_id=server_id)

        return self.call(context, msg)

    # TSIG Key Methods
    def create_tsigkey(self, context, values):
        msg = self.make_msg('create_tsigkey', values=values)

        return self.call(context, msg)

    def get_tsigkeys(self, context, criterion=None):
        msg = self.make_msg('get_tsigkeys', criterion=criterion)

        return self.call(context, msg)

    def get_tsigkey(self, context, tsigkey_id):
        msg = self.make_msg('get_tsigkey', tsigkey_id=tsigkey_id)

        return self.call(context, msg)

    def update_tsigkey(self, context, tsigkey_id, values):
        msg = self.make_msg('update_tsigkey', tsigkey_id=tsigkey_id,
                            values=values)

        return self.call(context, msg)

    def delete_tsigkey(self, context, tsigkey_id):
        msg = self.make_msg('delete_tsigkey', tsigkey_id=tsigkey_id)

        return self.call(context, msg)

    # Domain Methods
    def create_domain(self, context, values):
        msg = self.make_msg('create_domain', values=values)

        return self.call(context, msg)

    def get_domains(self, context, criterion=None):
        msg = self.make_msg('get_domains', criterion=criterion)

        return self.call(context, msg)

    def get_domain(self, context, domain_id):
        msg = self.make_msg('get_domain', domain_id=domain_id)

        return self.call(context, msg)

    def update_domain(self, context, domain_id, values, increment_serial=True):
        msg = self.make_msg('update_domain',
                            domain_id=domain_id,
                            values=values,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    def delete_domain(self, context, domain_id):
        msg = self.make_msg('delete_domain', domain_id=domain_id)

        return self.call(context, msg)

    def touch_domain(self, context, domain_id):
        msg = self.make_msg('touch_domain', domain_id=domain_id)

        return self.call(context, msg)

    def get_domain_servers(self, context, domain_id):
        msg = self.make_msg('get_domain_servers', domain_id=domain_id)

        return self.call(context, msg)

    # Record Methods
    def create_record(self, context, domain_id, values, increment_serial=True):
        msg = self.make_msg('create_record',
                            domain_id=domain_id,
                            values=values,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    def get_records(self, context, domain_id, criterion=None):
        msg = self.make_msg('get_records',
                            domain_id=domain_id,
                            criterion=criterion)

        return self.call(context, msg)

    def get_record(self, context, domain_id, record_id):
        msg = self.make_msg('get_record',
                            domain_id=domain_id,
                            record_id=record_id)

        return self.call(context, msg)

    def update_record(self, context, domain_id, record_id, values,
                      increment_serial=True):
        msg = self.make_msg('update_record',
                            domain_id=domain_id,
                            record_id=record_id,
                            values=values,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    def delete_record(self, context, domain_id, record_id,
                      increment_serial=True):
        msg = self.make_msg('delete_record',
                            domain_id=domain_id,
                            record_id=record_id,
                            increment_serial=increment_serial)

        return self.call(context, msg)

    # Count Methods
    def count_domains(self, context, criterion=None):
        msg = self.make_msg('count_domains', criterion=criterion)

        return self.call(context, msg)

    def count_records(self, context, criterion=None):
        msg = self.make_msg('count_records', criterion=criterion)

        return self.call(context, msg)

    def count_tenants(self, context):
        msg = self.make_msg('count_tenants')

        return self.call(context, msg)

    # Sync Methods
    def sync_domains(self, context):
        msg = self.make_msg('sync_domains')

        return self.call(context, msg)

    def sync_domain(self, context, domain_id):
        msg = self.make_msg('sync_domains', domain_id=domain_id)

        return self.call(context, msg)

    def sync_record(self, context, domain_id, record_id):
        msg = self.make_msg('sync_domains',
                            domain_id=domain_id,
                            record_id=record_id)

        return self.call(context, msg)
