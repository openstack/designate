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
from designate.api import v1 as api_v1
from designate.api import middleware
from designate.tests.test_api import ApiTestCase


LOG = logging.getLogger(__name__)


class ApiV1Test(ApiTestCase):
    __test__ = False

    def setUp(self):
        super(ApiV1Test, self).setUp()

        # Create a Flask application
        self.app = api_v1.factory({})

        # Inject the FaultWrapper middleware
        self.app.wsgi_app = api_v1.FaultWrapperMiddleware(self.app.wsgi_app)

        # Inject the NoAuth middleware
        self.app.wsgi_app = middleware.NoAuthContextMiddleware(
            self.app.wsgi_app)

        # Obtain a test client
        self.client = self.app.test_client()

        # Create and start an instance of the central service
        self.central_service = self.get_central_service()
        self.central_service.start()

    def tearDown(self):
        self.central_service.stop()
        super(ApiV1Test, self).tearDown()
