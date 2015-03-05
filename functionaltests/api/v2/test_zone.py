"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import tempest_lib
import tempest_lib.base

from functionaltests.common.client import DesignateClient


class ZoneTest(tempest_lib.base.BaseTestCase):

    def __init__(self, *args, **kwargs):
        super(ZoneTest, self).__init__(*args, **kwargs)
        self.client = DesignateClient()

    def test_list_zones(self):
        resp, body = self.client.get('/v2/zones')
        self.assertEqual(resp.status, 200)
