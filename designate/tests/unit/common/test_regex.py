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

from designate.common import constants


class TestRegex(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_tldname_is_valid(self):
        valid_tldnames = [
            'com',
            'net',
            'org',
            'co.uk',
        ]

        for tldname in valid_tldnames:
            self.assertTrue(constants.RE_TLDNAME.match(tldname))

    def test_tldname_is_not_valid(self):
        invalid_tldnames = [
            # Invalid Formats
            'com.',
            '.com',
            # Trailing newline - Bug 1471158
            "com\n",
        ]

        for tldname in invalid_tldnames:
            self.assertFalse(constants.RE_TLDNAME.match(tldname))
