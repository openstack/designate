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

import time

import tempest_lib.base
from tempest_lib.exceptions import NotFound

from functionaltests.common.client import DesignateClient


class BaseDesignateTest(tempest_lib.base.BaseTestCase):

    def __init__(self, *args, **kwargs):
        super(BaseDesignateTest, self).__init__(*args, **kwargs)
        self.base_client = DesignateClient()

    def wait_for_condition(self, condition, interval=1, timeout=20):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if condition():
                return
            time.sleep(interval)
        raise Exception("Timed out after {0} seconds".format(timeout))

    def is_zone_active(self, zone_id):
        resp, model = self.client.get_zone(zone_id)
        self.assertEqual(resp.status, 200)
        if model.zone.status == 'ACTIVE':
            return True
        elif model.zone.status == 'ERROR':
            raise Exception("Saw ERROR status")
        return False

    def is_zone_404(self, zone_id):
        try:
            # tempest_lib rest client raises exceptions on bad status codes
            resp, model = self.client.get_zone(zone_id)
        except NotFound:
            return True
        return False
