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


from unittest import mock

import oslotest.base

from designate.manage import base


class TestManageBase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_init(self):
        manage_base = base.Commands()
        self.assertEqual('designate-manage', manage_base.context.request_id)
        self.assertEqual([''], manage_base.output_message)

    @mock.patch('builtins.print')
    def test_print_result(self, mock_print):
        manage_base = base.Commands()
        manage_base.output_message.append('foo')
        manage_base.output_message.append('bar')

        manage_base._print_result()

        self.assertIn(mock.call(''), mock_print.call_args_list)
        self.assertIn(mock.call('foo'), mock_print.call_args_list)
        self.assertIn(mock.call('bar'), mock_print.call_args_list)
