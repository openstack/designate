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
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common.rpc import service as rpc_service
from moniker import database
from moniker import utils
from moniker.agent import api as agent_api


LOG = logging.getLogger(__name__)


class Service(rpc_service.Service):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            host=cfg.CONF.host,
            topic=cfg.CONF.central_topic
        )

        super(Service, self).__init__(*args, **kwargs)

        self.init_database()

    def init_database(self):
        self.database = database.get_driver()

    # Server Methods
    def create_server(self, context, values):
        server = self.database.create_server(context, values)

        utils.notify(context, 'api', 'server.create', server)

        return server

    def get_servers(self, context):
        return self.database.get_servers(context)

    def get_server(self, context, server_id):
        return self.database.get_server(context, server_id)

    def update_server(self, context, server_id, values):
        server = self.database.update_server(context, server_id, values)

        utils.notify(context, 'api', 'server.update', server)

        return server

    def delete_server(self, context, server_id):
        server = self.database.get_server(context, server_id)

        utils.notify(context, 'api', 'server.delete', server)

        return self.database.delete_server(context, server_id)

    # Domain Methods
    def create_domain(self, context, values):
        values['tenant_id'] = context.tenant

        domain = self.database.create_domain(context, values)

        agent_api.create_domain(context, domain)
        utils.notify(context, 'api', 'domain.create', domain)

        return domain

    def get_domains(self, context):
        return self.database.get_domains(context)

    def get_domain(self, context, domain_id):
        return self.database.get_domain(context, domain_id)

    def update_domain(self, context, domain_id, values):
        domain = self.database.update_domain(context, domain_id, values)

        agent_api.update_domain(context, domain)
        utils.notify(context, 'api', 'domain.update', domain)

        return domain

    def delete_domain(self, context, domain_id):
        domain = self.database.get_domain(context, domain_id)

        agent_api.delete_domain(context, domain_id)
        utils.notify(context, 'api', 'domain.delete', domain)

        return self.database.delete_domain(context, domain_id)

    # Record Methods
    def create_record(self, context, domain_id, values):
        record = self.database.create_record(context, domain_id, values)

        domain = self.database.get_domain(context, domain_id)

        agent_api.create_record(context, domain, record)
        utils.notify(context, 'api', 'record.create', record)

        return record

    def get_records(self, context, domain_id):
        return self.database.get_records(context, domain_id)

    def get_record(self, context, domain_id, record_id):
        return self.database.get_record(context, record_id)

    def update_record(self, context, domain_id, record_id, values):
        record = self.database.update_record(context, record_id, values)

        domain = self.database.get_domain(context, domain_id)

        agent_api.update_record(context, domain, record)
        utils.notify(context, 'api', 'record.update', record)

        return record

    def delete_record(self, context, domain_id, record_id):
        record = self.database.get_record(context, record_id)

        domain = self.database.get_domain(context, domain_id)

        agent_api.delete_record(context, domain, record)
        utils.notify(context, 'api', 'record.delete', record)

        return self.database.delete_record(context, record_id)
