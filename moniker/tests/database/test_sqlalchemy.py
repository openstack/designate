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
from moniker.openstack.common import log as logging
from moniker.tests.database import DatabaseDriverTestCase
from moniker import exceptions

LOG = logging.getLogger(__name__)


class SqlalchemyTest(DatabaseDriverTestCase):
    __test__ = True

    def setUp(self):
        super(SqlalchemyTest, self).setUp()
        self.config(database_driver='sqlalchemy')

    # def create_server(self, **kwargs):
    #     context = kwargs.pop('context', self.get_admin_context())
    #     service = kwargs.pop('service', self.get_central_service())

    #     values = dict(
    #         name='ns1.example.org',
    #         ipv4='192.0.2.1',
    #         ipv6='2001:db8::1',
    #     )

    #     values.update(kwargs)

    #     return service.create_server(context, values=values)
