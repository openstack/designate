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

from designate.conf import opts
from designate.conf import worker


class TestConfOpts(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_opts_tupleize(self):
        self.assertEqual([('a', 'b')], opts._tupleize({'a': 'b'}))

    def test_opts_list(self):
        self.assertIsInstance(opts.list_opts(), list)

    @mock.patch('pkgutil.iter_modules')
    def test_opts_list_module_names(self, mock_iter_modules):
        mock_iter_modules.return_value = iter(
            [
                (None, 'api', False),
                (None, 'worker', False),
                (None, 'unknown', True),
            ]
        )

        self.assertEqual(['api', 'worker'], opts._list_module_names())

    def test_opts_import_modules(self):
        self.assertEqual([worker], opts._import_modules(['worker']))

    @mock.patch('importlib.import_module')
    def test_opts_import_invalid_module(self, mock_import_module):
        mock_import_module.return_value = None

        self.assertRaisesRegex(
            Exception,
            "The module 'designate.conf.invalid' should have a 'list_opts' "
            "function which returns the config options.",
            opts._import_modules, ['invalid']
        )
