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

from designate.cmd import status


class StatusTestCase(oslotest.base.BaseTestCase):
    @mock.patch('designate.cmd.status.upgradecheck.main')
    @mock.patch('designate.cmd.status.utils.find_config')
    def test_main(self, mock_find_config, mock_upgradecheck_main):
        mock_find_config.return_value = ['/etc/designate/designate.conf']
        mock_upgradecheck_main.return_value = 0

        result = status.main()

        self.assertEqual(0, result)
        mock_find_config.assert_called_once_with('designate.conf')
        mock_upgradecheck_main.assert_called_once()
