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
from oslo import messaging

from designate.openstack.common import log as logging
from designate import rpc


LOG = logging.getLogger(__name__)


class AgentAPI(object):
    """
    Client side of the agent Rpc API.

    API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.agent_topic

        target = messaging.Target(topic=topic, version=self.RPC_API_VERSION)
        self.client = rpc.get_client(target, version_cap='1.0')

    # Server Methods
    def create_server(self, context, server, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'create_server', server=server)

    def update_server(self, context, server, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.client.call(context, 'update_server', server=server)

    def delete_server(self, context, server, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'delete_server', server=server)

    # TSIG Key Methods
    def create_tsigkey(self, context, tsigkey, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'create_tsigkey', tsigkey=tsigkey)

    def update_tsigkey(self, context, tsigkey, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'update_tsigkey', tsigkey=tsigkey)

    def delete_tsigkey(self, context, tsigkey, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'delete_tsigkey', tsigkey=tsigkey)

    # Domain Methods
    def create_domain(self, context, domain, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'create_domain', domain=domain)

    def update_domain(self, context, domain, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'update_domain', domain=domain)

    def delete_domain(self, context, domain, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'delete_domain', domain=domain)

    # Record Methods
    def update_recordset(self, context, domain, recordset, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'update_recordset', domain=domain,
                          recordset=recordset)

    def delete_recordset(self, context, domain, recordset, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'delete_recordset', domain=domain,
                          recordset=recordset)

    def create_record(self, context, domain, recordset, record, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'create_record', domain=domain,
                          recordset=recordset, record=record)

    def update_record(self, context, domain, recordset, record, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'update_record', domain=domain,
                          recordset=recordset, record=record)

    def delete_record(self, context, domain, recordset, record, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'delete_record', domain=domain,
                          recordset=recordset, record=record)

    # Sync Methods
    def sync_domain(self, context, domain, records, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'sync_domain', domain=domain,
                          record=records)

    def sync_record(self, context, domain, record, host=None):
        cctxt = self.client.prepare(server=host)

        return cctxt.call(context, 'sync_record', domain=domain, record=record)
