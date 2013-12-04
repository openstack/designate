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


class AgentAPI(rpc_proxy.RpcProxy):
    """
    Client side of the agent Rpc API.

    API version history:

        1.0 - Initial version
    """
    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.agent_topic
        super(AgentAPI, self).__init__(topic=topic, default_version='1.0')

    # Server Methods
    def create_server(self, context, server):
        msg = self.make_msg('create_server', server=server)

        return self.call(context, msg)

    def update_server(self, context, server):
        msg = self.make_msg('update_server', server=server)

        return self.call(context, msg)

    def delete_server(self, context, server):
        msg = self.make_msg('delete_server', server=server)

        return self.call(context, msg)

    # TSIG Key Methods
    def create_tsigkey(self, context, tsigkey):
        msg = self.make_msg('create_tsigkey', tsigkey=tsigkey)

        return self.call(context, msg)

    def update_tsigkey(self, context, tsigkey):
        msg = self.make_msg('update_tsigkey', tsigkey=tsigkey)

        return self.call(context, msg)

    def delete_tsigkey(self, context, tsigkey):
        msg = self.make_msg('delete_tsigkey', tsigkey=tsigkey)

        return self.call(context, msg)

    # Domain Methods
    def create_domain(self, context, domain):
        msg = self.make_msg('create_domain', domain=domain)

        return self.call(context, msg)

    def update_domain(self, context, domain):
        msg = self.make_msg('update_domain', domain=domain)

        return self.call(context, msg)

    def delete_domain(self, context, domain):
        msg = self.make_msg('delete_domain', domain=domain)

        return self.call(context, msg)

    # Record Methods
    def create_record(self, context, domain, record):
        msg = self.make_msg('create_record',
                            domain=domain,
                            record=record)

        return self.call(context, msg)

    def update_record(self, context, domain, record):
        msg = self.make_msg('update_record',
                            domain=domain,
                            record=record)

        return self.call(context, msg)

    def delete_record(self, context, domain, record):
        msg = self.make_msg('delete_record',
                            domain=domain,
                            record=record)

        return self.call(context, msg)

    # Sync Methods
    def sync_domain(self, context, domain, records):
        msg = self.make_msg('sync_domains',
                            domain=domain,
                            records=records)

        return self.call(context, msg)

    def sync_record(self, context, domain, record):
        msg = self.make_msg('sync_domains',
                            domain=domain,
                            record=record)

        return self.call(context, msg)
