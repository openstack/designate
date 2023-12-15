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


from oslo_config import fixture as cfg_fixture
import oslotest.base
import webtest

from designate.api import versions
from designate.common import constants
import designate.conf


CONF = designate.conf.CONF


class TestApiVersion(oslotest.base.BaseTestCase):

    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    def test_add_a_version(self):
        api_url = 'http://203.0.113.1/v2'
        results = []

        versions._add_a_version(
            results, 'v2.1', api_url, constants.EXPERIMENTAL,
            '2022-08-10T00:00:00Z')

        self.assertEqual(1, len(results))
        self.assertEqual('v2.1', results[0]['id'])
        self.assertEqual(constants.EXPERIMENTAL, results[0]['status'])
        self.assertEqual('2022-08-10T00:00:00Z', results[0]['updated'])
        self.assertEqual(2, len(results[0]['links']))

    def test_get_versions(self):
        CONF.set_override('enable_host_header', False, 'service:api')
        CONF.set_override(
            'api_base_uri', 'http://203.0.113.1:9001/', 'service:api'
        )

        self.app = versions.factory({})
        self.client = webtest.TestApp(self.app)

        response = self.client.get('/')
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual(3, len(response.json['versions']))
        self.assertEqual(
            'http://203.0.113.1:9001/v2',
            response.json['versions'][0]['links'][0]['href']
        )

    def test_get_versions_with_enable_host_header(self):
        CONF.set_override('enable_host_header', True, 'service:api')

        self.app = versions.factory({})
        self.client = webtest.TestApp(self.app)

        response = self.client.get('/')
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual(3, len(response.json['versions']))
        self.assertEqual(
            'http://localhost/v2',
            response.json['versions'][0]['links'][0]['href']
        )
