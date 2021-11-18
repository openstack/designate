# Copyright 2019 Inspur
#
# Author: ZhouHeng <zhouhenglc@inspur.com>
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

from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import oslotest.base


from designate import dnsutils
from designate.mdns import xfr
from designate import objects
from designate.tests import fixtures


CONF = cfg.CONF


class MdnsXFRMixinTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super(MdnsXFRMixinTest, self).setUp()
        self.stdlog = fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))
        self.context = mock.Mock()
        self.tg = mock.Mock()
        self.xfrMixin = xfr.XFRMixin()
        self.xfrMixin.central_api = mock.Mock()

    def test_zone_sync_not_change_name(self):
        zone = objects.Zone(id='7592878e-4ade-40de-8b8d-699b871ee6fa',
                            name="example.com.",
                            serial=1,
                            masters=objects.ZoneMasterList.from_list([
                                {'host': '127.0.0.1', 'port': 53}, ]))

        with mock.patch.object(dnsutils, 'do_axfr') as mock_axfr, \
                mock.patch.object(dnsutils, 'from_dnspython_zone') as mock2:
            mock_axfr.return_value = mock.Mock()
            mock2.return_value = zone
            self.xfrMixin.zone_sync(self.context, zone)

            self.assertIn("transferred_at", zone.obj_what_changed())
            self.assertNotIn("name", zone.obj_what_changed())
