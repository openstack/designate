# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from designate.backend import base
from designate.agent import rpcapi as agent_rpcapi


class RPCBackend(base.Backend):
    def __init__(self, central_service):
        super(RPCBackend, self).__init__(central_service)
        self.agent_api = agent_rpcapi.AgentAPI()

    def create_tsigkey(self, context, tsigkey):
        return self.agent_api.create_tsigkey(context, tsigkey)

    def update_tsigkey(self, context, tsigkey):
        return self.agent_api.update_tsigkey(context, tsigkey)

    def delete_tsigkey(self, context, tsigkey):
        return self.agent_api.delete_tsigkey(context, tsigkey)

    def create_server(self, context, server):
        return self.agent_api.create_server(context, server)

    def update_server(self, context, server):
        return self.agent_api.update_server(context, server)

    def delete_server(self, context, server):
        return self.agent_api.delete_server(context, server)

    def create_domain(self, context, domain):
        return self.agent_api.create_domain(context, domain)

    def update_domain(self, context, domain):
        return self.agent_api.update_domain(context, domain)

    def delete_domain(self, context, domain):
        return self.agent_api.delete_domain(context, domain)

    def update_recordset(self, context, domain, recordset):
        return self.agent_api.update_recordset(context, domain, recordset)

    def delete_recordset(self, context, domain, recordset):
        return self.agent_api.delete_recordset(context, domain, recordset)

    def create_record(self, context, domain, recordset, record):
        return self.agent_api.create_record(context, domain, recordset, record)

    def update_record(self, context, domain, recordset, record):
        return self.agent_api.update_record(context, domain, recordset, record)

    def delete_record(self, context, domain, recordset, record):
        return self.agent_api.delete_record(context, domain, recordset, record)

    def sync_domain(self, context, domain, records):
        return self.agent_api.sync_domain(context, domain, records)

    def sync_record(self, context, domain, record):
        return self.agent_api.sync_record(context, domain, record)
