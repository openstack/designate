# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
from oslo_config import cfg

from designate import coordination
from designate import service
from designate.tests import TestCase

cfg.CONF.register_group(cfg.OptGroup("service:dummy"))

cfg.CONF.register_opts([
], group="service:dummy")


class CoordinatedService(coordination.CoordinationMixin, service.Service):
    @property
    def service_name(self):
        return "dummy"


class CoordinationMixinTests(TestCase):
    def setUp(self):
        super(CoordinationMixinTests, self).setUp()
        self.config(backend_url="zake://", group="coordination")

    def test_start(self):
        service = CoordinatedService()
        service.start()

        self.assertEqual(True, service._coordination_started)
        self.assertIn(service.service_name,
                      service._coordinator.get_groups().get())
        self.assertIn(service._coordination_id,
                      service._coordinator.get_members(
                            service.service_name).get())

    def test_stop(self):
        service = CoordinatedService()
        service.start()
        service.stop()
        self.assertEqual(False, service._coordination_started)

    def test_start_no_coordination(self):
        self.config(backend_url=None, group="coordination")
        service = CoordinatedService()
        service.start()
        self.assertEqual(None, service._coordinator)

    def test_stop_no_coordination(self):
        self.config(backend_url=None, group="coordination")
        service = CoordinatedService()
        self.assertEqual(None, service._coordinator)
        service.start()
        service.stop()
