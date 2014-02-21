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
from designate.openstack.common import log as logging
from designate import storage
from designate.tests import TestCase
from designate.tests.test_storage import StorageTestCase

LOG = logging.getLogger(__name__)


class SqlalchemyStorageTest(StorageTestCase, TestCase):
    def setUp(self):
        super(SqlalchemyStorageTest, self).setUp()

        self.config(
            storage_driver='sqlalchemy',
            group='service:central'
        )

        self.storage = storage.get_storage()
