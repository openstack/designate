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


import os

from designate.manage import tlds
from designate.tests import base_fixtures
import designate.tests.functional
from designate.tests import resources


def get_tlds_path(name='tlds_list'):
    return os.path.join(resources.path, 'tlds', name)


class ManageTLDSTestCase(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.tlds = tlds.TLDCommands()

    def test_import_tlds(self):
        self.tlds.from_file(get_tlds_path(), ',')

        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(5, len(tlds))
        for tld in tlds:
            self.assertFalse(tld.description)

        self.assertNotIn('Number of errors', self.stdlog.logger.output)

    def test_import_tlds_with_descriptions(self):
        self.tlds.from_file(get_tlds_path('tlds_list_with_descriptions'), ',')

        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(5, len(tlds))
        for tld in tlds:
            self.assertTrue(tld.description)

        self.assertNotIn('Number of errors', self.stdlog.logger.output)

    def test_import_tlds_with_extra_fields(self):
        self.tlds.from_file(get_tlds_path('tlds_list_with_extra_fields'), ',')

        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(0, len(tlds))

        self.assertIn('InvalidLine -->', self.stdlog.logger.output)
        self.assertIn('Number of errors', self.stdlog.logger.output)

    def test_import_tlds_with_invalid_tlds(self):
        self.tlds.from_file(get_tlds_path('tlds_list_with_invalid_tlds'), ',')

        tlds = self.central_service.find_tlds(self.admin_context)
        self.assertEqual(1, len(tlds))

        self.assertIn('InvalidTld -->', self.stdlog.logger.output)
        self.assertIn('InvalidDescription -->', self.stdlog.logger.output)
        self.assertIn('DuplicateTld -->', self.stdlog.logger.output)
        self.assertIn('Number of errors', self.stdlog.logger.output)

    def test_import_tlds_file_does_not_exist(self):
        self.assertRaisesRegex(
            Exception,
            'TLD Input file Not Found',
            self.tlds.from_file, get_tlds_path('invalid_file'), ','
        )
