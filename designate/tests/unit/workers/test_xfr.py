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

from oslo_config import fixture as cfg_fixture
import oslotest.base

from designate.common import constants
import designate.conf
from designate import dnsutils
from designate import exceptions
from designate import objects
from designate.tests import base_fixtures
from designate.worker.tasks import zone as worker_zone


CONF = designate.conf.CONF


class TestXfr(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.stdlog = base_fixtures.StandardLogging()
        self.useFixture(self.stdlog)
        self.useFixture(cfg_fixture.Config(CONF))
        self.context = mock.Mock()

    @mock.patch.object(dnsutils, 'do_axfr', mock.Mock())
    def test_zone_sync_not_change_name(self):
        zone = objects.Zone(
            id='7592878e-4ade-40de-8b8d-699b871ee6fa',
            name='example.com.',
            serial=1,
            masters=objects.ZoneMasterList.from_list(
                [{'host': '203.0.113.1', 'port': 53}, ]
            ),
            type=constants.ZONE_SECONDARY,
        )

        self.xfr = worker_zone.ZoneXfr(mock.Mock(), self.context, zone)
        self.xfr._central_api = mock.Mock()

        with mock.patch.object(dnsutils, 'from_dnspython_zone') as mock_dns:
            mock_dns.return_value = zone

            self.xfr()

            self.assertIn('transferred_at', zone.obj_what_changed())
            self.assertNotIn('name', zone.obj_what_changed())

    @mock.patch.object(dnsutils, 'do_axfr', mock.Mock())
    def test_zone_sync_not_change_masters(self):
        recordset = objects.RecordSet(
            name='www.example.test.', type='TXT',
            records=objects.RecordList(objects=[
                objects.Record(data='foo bar'),
            ])
        )
        zone = objects.Zone(
            id='7592878e-4ade-40de-8b8d-699b871ee6fa',
            name='example.com.',
            serial=1,
            masters=objects.ZoneMasterList.from_list(
                [{'host': '203.0.113.1', 'port': 53}, ]
            ),
            type=constants.ZONE_SECONDARY,
            recordsets=objects.RecordSetList(objects=[]),
        )

        self.xfr = worker_zone.ZoneXfr(mock.Mock(), self.context, zone)
        self.xfr._central_api = mock.Mock()

        with mock.patch.object(dnsutils, 'from_dnspython_zone') as mock_dns:
            zone.recordsets = objects.RecordSetList(objects=[recordset])
            zone.masters = objects.ZoneMasterList()
            mock_dns.return_value = zone

            self.xfr()

            self.assertIn('transferred_at', zone.obj_what_changed())
            self.assertNotIn('masters', zone.obj_what_changed())

    @mock.patch.object(dnsutils, 'do_axfr', mock.Mock())
    def test_zone_sync_using_list_of_servers(self):
        zone = objects.Zone(
            id='7592878e-4ade-40de-8b8d-699b871ee6fa',
            name='example.com.',
            serial=1,
            type=constants.ZONE_SECONDARY,
        )

        self.xfr = worker_zone.ZoneXfr(
            mock.Mock(), self.context, zone,
            servers=[{'host': '203.0.113.1', 'port': 53}, ]
        )
        self.xfr._central_api = mock.Mock()

        with mock.patch.object(dnsutils, 'from_dnspython_zone') as mock_dns:
            mock_dns.return_value = zone

            self.xfr()

            self.assertIn('transferred_at', zone.obj_what_changed())
            self.assertNotIn('name', zone.obj_what_changed())

    @mock.patch.object(dnsutils, 'do_axfr', side_effect=exceptions.XFRFailure)
    def test_zone_sync_axfr_failure(self, _):
        zone = objects.Zone(
            id='7592878e-4ade-40de-8b8d-699b871ee6fa',
            name='example.com.',
            serial=1,
            masters=objects.ZoneMasterList.from_list(
                [{'host': '203.0.113.1', 'port': 53}, ]
            ),
            type=constants.ZONE_SECONDARY,
        )

        self.xfr = worker_zone.ZoneXfr(mock.Mock(), self.context, zone)
        self.xfr._central_api = mock.Mock()

        with mock.patch.object(dnsutils, 'from_dnspython_zone') as mock_dns:
            mock_dns.return_value = zone

            self.xfr()

            self.assertNotIn('transferred_at', zone.obj_what_changed())

    @mock.patch.object(dnsutils, 'do_axfr')
    def test_zone_only_allow_axfr_on_secondary_zones(self, mock_do_axfr):
        zone = objects.Zone(
            id='7592878e-4ade-40de-8b8d-699b871ee6fa',
            name='example.com.',
            serial=1,
            masters=objects.ZoneMasterList.from_list(
                [{'host': '203.0.113.1', 'port': 53}, ]
            ),
            type=constants.ZONE_PRIMARY,
        )

        self.xfr = worker_zone.ZoneXfr(mock.Mock(), self.context, zone)
        self.xfr._central_api = mock.Mock()

        self.xfr()

        mock_do_axfr.assert_not_called()
