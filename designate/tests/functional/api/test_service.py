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
from unittest import mock


from paste import urlmap

from designate.api import service
from designate import exceptions
import designate.tests.functional


class ApiServiceTest(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()

        self.config(listen=['0.0.0.0:0'], group='service:api')

        self.service = service.Service()

    def test_start_and_stop(self):
        # NOTE: Start is already done by the fixture in start_service()
        self.service.start()
        self.service.stop()

    def test_get_wsgi_application(self):
        self.assertIsInstance(self.service.wsgi_application, urlmap.URLMap)

    @mock.patch('designate.utils.find_config')
    def test_unable_to_find_config(self, mock_find_config):
        mock_find_config.return_value = list()
        with self.assertRaisesRegex(
                exceptions.ConfigurationError,
                'Unable to determine appropriate api-paste-config file'):
            self.assertFalse(self.service.wsgi_application)
