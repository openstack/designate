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

cfg.CONF.register_opts([
    cfg.StrOpt('database-driver', default='sqlalchemy',
               help='The database driver to use'),
])


class BaseDatabase(object):
    def create_server(self, context, values):
        raise NotImplementedError()

    def get_servers(self, context):
        raise NotImplementedError()

    def get_server(self, context, server_id):
        raise NotImplementedError()

    def update_server(self, context, server_id, values):
        raise NotImplementedError()

    def delete_server(self, context, server_id):
        raise NotImplementedError()

    def create_domain(self, context, values):
        raise NotImplementedError()

    def get_domains(self, context):
        raise NotImplementedError()

    def get_domain(self, context, domain_id):
        raise NotImplementedError()

    def update_domain(self, context, domain_id, values):
        raise NotImplementedError()

    def delete_domain(self, context, domain_id):
        raise NotImplementedError()

    def create_record(self, context, domain_id, values):
        raise NotImplementedError()

    def get_records(self, context, domain_id):
        raise NotImplementedError()

    def get_record(self, context, record_id):
        raise NotImplementedError()

    def update_record(self, context, record_id, values):
        raise NotImplementedError()

    def delete_record(self, context, record_id):
        raise NotImplementedError()


def get_driver(*args, **kwargs):
    # TODO: Switch to the config var + entry point loading
    from moniker.database.sqlalchemy import Sqlalchemy

    return Sqlalchemy(*args, **kwargs)


def reinitialize(*args, **kwargs):
    """ Reset the DB to default - Used for testing purposes """
    from moniker.database.sqlalchemy.session import reset_session
    reset_session(*args, **kwargs)
