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

import designate.conf
from designate.storage import sqlalchemy


CONF = designate.conf.CONF


class SqlalchemyTestCase(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

        self.storage = sqlalchemy.SQLAlchemyStorage()

    def test_rname_check(self):
        self.assertEqual(
            {'name': 'foo'}, self.storage._rname_check({'name': 'foo'})
        )

    def test_rname_check_reverse_name(self):
        self.assertEqual(
            {'reverse_name': 'oof*'},
            self.storage._rname_check({'name': '*foo'})
        )
