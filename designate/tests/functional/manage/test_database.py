# Copyright 2022 Red Hat
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


from io import StringIO
from unittest import mock

from designate.manage import database
import designate.tests.functional


class TestManageDatabase(designate.tests.functional.TestCase):

    def setUp(self):
        super().setUp()
        self.stdlog = designate.tests.base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)

        self.db_cmds = database.DatabaseCommands()

    def test_current(self):
        cmd_output = StringIO()
        self.db_cmds.current(stringio_buffer=cmd_output)
        self.assertIn('head', cmd_output.getvalue())

    def test_heads(self):
        cmd_output = StringIO()
        self.db_cmds.heads(stringio_buffer=cmd_output)
        self.assertIn('head', cmd_output.getvalue())

    def test_history(self):
        cmd_output = StringIO()
        self.db_cmds.history(stringio_buffer=cmd_output)
        self.assertIn('head', cmd_output.getvalue())

    def test_version(self):
        with mock.patch('sys.stdout', new=StringIO()) as cmd_output:
            self.db_cmds.version()
            self.assertIn('head', cmd_output.getvalue())

    def test_sync(self):
        cmd_output = StringIO()
        self.db_cmds.sync(stringio_buffer=cmd_output)
        # The test framework will run the migration, so there should be
        # no output of this command run.
        self.assertEqual('', cmd_output.getvalue())

    def test_upgrade(self):
        cmd_output = StringIO()
        self.db_cmds.upgrade('head', stringio_buffer=cmd_output)
        # The test framework will run the migration, so there should be
        # no output of this command run.
        self.assertEqual('', cmd_output.getvalue())
