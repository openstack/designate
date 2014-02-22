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

        # Inject the TestContext middleware
        self.app = middleware.TestContextMiddleware(
            self.app, self.admin_context.tenant_id,
            self.admin_context.tenant_id)

        # Obtain a test client
        self.client = TestApp(self.app)

        # Create and start an instance of the central service
        self.central_service = self.start_service('central')

    def tearDown(self):
        self.app = None
        self.client = None

        super(ApiV2TestCase, self).tearDown()

    def _assert_paging(self, data, url, key=None, limit=5, sort_dir='asc',
                       sort_key='created_at', marker=None, status=200):
        def _page(marker=None):
            params = {'limit': limit,
                      'sort_dir': sort_dir,
                      'sort_key': sort_key}

            if marker is not None:
                params['marker'] = marker

            r = self.client.get(url, params, status=status)
            if status != 200:
                return r
            else:
                return r.json[key] if key in r.json else r.json

        page_items = _page(marker=marker)
        if status != 200:
            return page_items

        x = 0
        length = len(data)
        for i in xrange(0, length):
            assert data[i]['id'] == page_items[x]['id']

            x += 1
            # Don't bother getting a new page if we're at the last item
            if x == len(page_items) and i != length - 1:
                x = 0
                page_items = _page(page_items[-1:][0]['id'])

        _page(marker=page_items[-1:][0]['id'])
