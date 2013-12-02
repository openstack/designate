# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from webtest import TestApp
from designate.openstack.common import log as logging
from designate.api import v2 as api_v2
from designate.api import middleware
from designate.tests.test_api import ApiTestCase


LOG = logging.getLogger(__name__)


class ApiV2TestCase(ApiTestCase):
    def setUp(self):
        super(ApiV2TestCase, self).setUp()

        # Ensure the v2 API is enabled
        self.config(enable_api_v2=True, group='service:api')

        # Create the application
        self.app = api_v2.factory({})

        # Inject the FaultWrapper middleware
        self.app = middleware.FaultWrapperMiddleware(self.app)

        # Inject the NoAuth middleware
        self.app = middleware.NoAuthContextMiddleware(self.app)

        # Obtain a test client
        self.client = TestApp(self.app)

        # Create and start an instance of the central service
        self.central_service = self.start_service('central')

    def tearDown(self):
        self.app = None
        self.client = None

        super(ApiV2TestCase, self).tearDown()
