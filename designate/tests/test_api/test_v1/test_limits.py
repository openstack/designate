# coding=utf-8
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
from oslo_log import log as logging

from designate.tests.test_api.test_v1 import ApiV1Test


LOG = logging.getLogger(__name__)


class ApiV1LimitsTest(ApiV1Test):
    def test_get_limits_schema(self):
        response = self.get('/schemas/limits')
        self.assertIn('id', response.json)
        self.assertIn('description', response.json)
        self.assertIn('title', response.json)
        self.assertIn('additionalProperties', response.json)
        self.assertIn('properties', response.json)

    def test_get_limits(self):
        response = self.get('/limits')
        self.assertIn('limits', response.json)
        self.assertIn('absolute', response.json['limits'])
        self.assertIn('maxDomains', response.json['limits']['absolute'])
        self.assertIn('maxDomainRecords', response.json['limits']['absolute'])
