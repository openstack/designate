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
import testtools

from designate.api.v2 import patches
from designate import exceptions


class TestPatches(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.environ = {
            'CONTENT_TYPE': 'application/json',
        }
        self.request = patches.Request(self.environ)

    def test_unsupported_content_type(self):
        self.environ['CONTENT_TYPE'] = 'invalid'

        with testtools.ExpectedException(exceptions.UnsupportedContentType):
            self.assertIsNone(self.request.body_dict)

    @mock.patch('oslo_serialization.jsonutils.load')
    def test_request_body_empty(self, mock_load):
        mock_load.side_effect = ValueError()

        with testtools.ExpectedException(exceptions.EmptyRequestBody):
            self.assertIsNone(self.request.body_dict)

    @mock.patch('oslo_serialization.jsonutils.load')
    def test_invalid_json(self, mock_load):
        mock_load.side_effect = ValueError()
        self.request.body = b'invalid'

        with testtools.ExpectedException(exceptions.InvalidJson):
            self.assertIsNone(self.request.body_dict)
