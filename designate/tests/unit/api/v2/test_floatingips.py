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


import oslotest.base

from designate.api.v2.controllers import floatingips
from designate import exceptions


class FloatingIPTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_fip_key_to_data(self):
        self.assertEqual(
            ('RegionOne', '2fc6745d-1631-4f34-b13d-90f9014236c0'),
            floatingips.fip_key_to_data(
                'RegionOne:2fc6745d-1631-4f34-b13d-90f9014236c0'
            )
        )
        self.assertEqual(
            ('RegionTwo', '2fc6745d-1631-4f34-b13d-90f9014236c0'),
            floatingips.fip_key_to_data(
                'RegionTwo:2fc6745d-1631-4f34-b13d-90f9014236c0'
            )
        )

        self.assertEqual(
            ('region-one', '2fc6745d-1631-4f34-b13d-90f9014236c0'),
            floatingips.fip_key_to_data(
                'region-one:2fc6745d-1631-4f34-b13d-90f9014236c0'
            )
        )
        self.assertEqual(
            ('region-1', '2fc6745d-1631-4f34-b13d-90f9014236c0'),
            floatingips.fip_key_to_data(
                'region-1:2fc6745d-1631-4f34-b13d-90f9014236c0'
            )
        )
        self.assertEqual(
            ('region-1-test', '2fc6745d-1631-4f34-b13d-90f9014236c0'),
            floatingips.fip_key_to_data(
                'region-1-test:2fc6745d-1631-4f34-b13d-90f9014236c0'
            )
        )
        self.assertEqual(
            ('region.1.test', '2fc6745d-1631-4f34-b13d-90f9014236c0'),
            floatingips.fip_key_to_data(
                'region.1.test:2fc6745d-1631-4f34-b13d-90f9014236c0'
            )
        )
        self.assertEqual(
            ('region.test', '2fc6745d-1631-4f34-b13d-90f9014236c0'),
            floatingips.fip_key_to_data(
                'region.test:2fc6745d-1631-4f34-b13d-90f9014236c0'
            )
        )

    def test_fip_key_to_data_bad_request(self):
        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Floating IP invalid is not in the format of <region>:<uuid>',
            floatingips.fip_key_to_data, 'invalid'
        )
        self.assertRaisesRegex(
            exceptions.BadRequest,
            'Floating IP :2fc6745d-1631-4f34-b13d-90f9014236c0 is not in the '
            'format of <region>:<uuid>',
            floatingips.fip_key_to_data,
            ':2fc6745d-1631-4f34-b13d-90f9014236c0'
        )
