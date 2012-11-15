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
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.tests import TestCase
from moniker import backend

LOG = logging.getLogger(__name__)


class BackendDriverTestCase(TestCase):
    __test__ = False

    def get_backend_driver(self):
        return backend.get_backend(cfg.CONF)

    def setUp(self):
        super(BackendDriverTestCase, self).setUp()
        self.backend = self.get_backend_driver()

    def test_dummy(self):
        # Right now we just check that we can instantiate the driver via the
        # setUp above. Proper tests TODO.
        pass
