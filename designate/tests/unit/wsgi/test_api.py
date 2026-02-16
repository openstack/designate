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


class WSGIApiTestCase(oslotest.base.BaseTestCase):
    @mock.patch('designate.api.wsgi.init_application')
    def test_wsgi_api_application(self, mock_init_app):
        mock_init_app.return_value = mock.Mock()

        # Import the module to test the module-level code
        import designate.wsgi.api

        # Verify the application was initialized
        self.assertIsNotNone(designate.wsgi.api.application)
        mock_init_app.assert_called_once()
