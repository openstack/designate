# Copyright 2014 Cloudwatt
#
# Author: Jordan Pittier <jordan.pittier@cloudwatt.com>
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

from designate.tests import TestCase
from designate import utils


LOG = logging.getLogger(__name__)


class Bind9Test(TestCase):
    def test_bind9_zone_ends_with_empty_line(self):
        name = ['templates', 'bind9-zone.jinja2']
        resource_string = utils.resource_string(*name)
        self.assertEqual(b'\n\n', resource_string[-2:])
