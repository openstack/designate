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
import itertools

from oslo_log import log as logging
from webtest import TestApp

from designate.api import v2 as api_v2
from designate.api import middleware
from designate.tests.test_api import ApiTestCase


LOG = logging.getLogger(__name__)


INVALID_ID = [
    '2fdadfb1-cf96-4259-ac6b-bb7b6d2ff98g',
    '2fdadfb1cf964259ac6bbb7b6d2ff9GG',
    '12345'
]


class ApiV2TestCase(ApiTestCase):
    def setUp(self):
        super(ApiV2TestCase, self).setUp()

        # Ensure the v2 API is enabled
        self.config(enable_api_v2=True, group='service:api')

        # Create the application
        self.app = api_v2.factory({})

        # Inject the NormalizeURIMiddleware middleware
        self.app = middleware.NormalizeURIMiddleware(self.app)

        # Inject the ValidationError middleware
        self.app = middleware.APIv2ValidationErrorMiddleware(self.app)

        # Inject the FaultWrapper middleware
        self.app = middleware.FaultWrapperMiddleware(self.app)

        # Inject the TestContext middleware
        self.app = middleware.TestContextMiddleware(
            self.app, self.admin_context.tenant,
            self.admin_context.tenant)

        # Obtain a test client
        self.client = TestApp(self.app)

    def tearDown(self):
        self.app = None
        self.client = None

        super(ApiV2TestCase, self).tearDown()

    def _assert_invalid_uuid(self, method, url_format, *args, **kw):
        """
        Test that UUIDs used in the URL is valid.
        """
        count = url_format.count('%s')
        for i in itertools.product(INVALID_ID, repeat=count):
            self._assert_exception('invalid_uuid', 400, method, url_format % i)

    def _assert_exception(self, expected_type, expected_status, obj,
                          *args, **kwargs):
        """
        Checks the response that a api call with a exception contains the
        wanted data.
        """
        kwargs.setdefault('status', expected_status)

        response = obj(*args, **kwargs) if not hasattr(obj, 'json') else obj

        self.assertEqual(expected_status, response.json['code'])
        self.assertEqual(expected_type, response.json['type'])

    def _assert_invalid_paging(self, data, url, key):
        """
        Test that certain circumstances is invalid for paging in a given url.
        """
        self._assert_paging(data, url, key=key,
                            limit='invalid_limit',
                            expected_type='invalid_limit',
                            expected_status=400)

        self._assert_paging(data, url, key=key,
                            sort_dir='invalid_sort_dir',
                            expected_type='invalid_sort_dir',
                            expected_status=400)

        self._assert_paging(data, url, key=key,
                            sort_key='invalid_sort_key',
                            expected_type='invalid_sort_key',
                            expected_status=400)

        self._assert_paging(data, url, key=key,
                            marker='invalid_marker',
                            expected_type='invalid_marker',
                            expected_status=400)

    def _assert_paging(self, data, url, key=None, limit=5, sort_dir='asc',
                       sort_key='created_at', marker=None,
                       expected_type=None, expected_status=200):

        def _page(marker=None):
            params = {'limit': limit,
                      'sort_dir': sort_dir,
                      'sort_key': sort_key}

            if marker is not None:
                params['marker'] = marker

            r = self.client.get(url, params, status=expected_status)
            if expected_status != 200:
                if expected_type:
                    self._assert_exception(expected_type, expected_status, r)
                return r
            else:
                return r.json[key] if key in r.json else r.json

        response = _page(marker=marker)
        if expected_status != 200:
            if expected_type:
                self._assert_exception(expected_type, expected_status,
                                       response)

            return response

        x = 0
        length = len(data)
        for i in range(0, length):
            assert data[i]['id'] == response[x]['id']

            x += 1
            # Don't bother getting a new page if we're at the last item
            if x == len(response) and i != length - 1:
                x = 0
                response = _page(response[-1:][0]['id'])

        _page(marker=response[-1:][0]['id'])
