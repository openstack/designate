# Copyright 2015 FUJITSU LIMITED
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

import mock

from designate import objects
from designate.tests.test_backend import BackendTestCase
from designate.backend.impl_bind9 import Bind9Backend

# TODO(Federico): test execute() calls


class Bind9BackendTestCase(BackendTestCase):

    def setUp(self):
        super(Bind9BackendTestCase, self).setUp()

        self.zone = objects.Zone(id='cca7908b-dad4-4c50-adba-fb67d4c556e8',
                                 name='example.com.',
                                 email='example@example.com')

        target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'powerdns',
            'masters': [{'host': '192.0.2.1', 'port': 53},
                        {'host': '192.0.2.2', 'port': 35}],
            'options': [{'key': 'host', 'value': '192.0.2.3'},
                        {'key': 'port', 'value': 53},
                        {'key': 'rndc_host', 'value': '192.0.2.4'},
                        {'key': 'rndc_port', 'value': 953},
                        {'key': 'rndc_config_file', 'value': '/etc/rndc.conf'},
                        {'key': 'rndc_key_file', 'value': '/etc/rndc.key'},
                        {'key': 'clean_zonefile', 'value': 'true'}],
        })

        self.backend = Bind9Backend(target)

    @mock.patch('designate.utils.execute')
    def test_create_zone(self, execute):
        context = self.get_context()
        self.backend.create_zone(context, self.zone)

    @mock.patch('designate.utils.execute')
    def test_delete_zone(self, execute):
        context = self.get_context()
        self.backend.delete_zone(context, self.zone)
