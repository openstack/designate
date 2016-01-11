# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from testscenarios import load_tests_apply_scenarios as load_tests  # noqa
import testtools
from oslo_config import cfg
from oslo_log import log as logging

from designate import quota
from designate import tests
from designate import exceptions


LOG = logging.getLogger(__name__)


class QuotaTestCase(tests.TestCase):
    scenarios = [
        ('noop', dict(quota_driver='noop')),
        ('storage', dict(quota_driver='storage'))
    ]

    def setUp(self):
        super(QuotaTestCase, self).setUp()
        self.config(quota_driver=self.quota_driver)
        self.quota = quota.get_quota()

    def test_get_quotas(self):
        context = self.get_admin_context()

        quotas = self.quota.get_quotas(context, 'DefaultQuotaTenant')

        self.assertIsNotNone(quotas)
        self.assertEqual({
            'api_export_size': cfg.CONF.quota_api_export_size,
            'zones': cfg.CONF.quota_zones,
            'zone_recordsets': cfg.CONF.quota_zone_recordsets,
            'zone_records': cfg.CONF.quota_zone_records,
            'recordset_records': cfg.CONF.quota_recordset_records,
        }, quotas)

    def test_limit_check_unknown(self):
        context = self.get_admin_context()

        with testtools.ExpectedException(exceptions.QuotaResourceUnknown):
            self.quota.limit_check(context, 'tenant_id', unknown=0)

        with testtools.ExpectedException(exceptions.QuotaResourceUnknown):
            self.quota.limit_check(context, 'tenant_id', unknown=0, zones=0)

    def test_limit_check_under(self):
        context = self.get_admin_context()

        self.quota.limit_check(context, 'tenant_id', zones=0)
        self.quota.limit_check(context, 'tenant_id', zone_records=0)
        self.quota.limit_check(context, 'tenant_id', zones=0,
                               zone_records=0)

        self.quota.limit_check(context, 'tenant_id',
                               zones=(cfg.CONF.quota_zones - 1))
        self.quota.limit_check(
            context,
            'tenant_id',
            zone_records=(cfg.CONF.quota_zone_records - 1))

    def test_limit_check_at(self):
        context = self.get_admin_context()

        with testtools.ExpectedException(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id',
                                   zones=cfg.CONF.quota_zones)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.quota.limit_check(
                context,
                'tenant_id',
                zone_records=cfg.CONF.quota_zone_records)

    def test_limit_check_over(self):
        context = self.get_admin_context()

        with testtools.ExpectedException(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', zones=99999)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', zone_records=99999)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', zones=99999,
                                   zone_records=99999)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', zones=99999,
                                   zone_records=0)

        with testtools.ExpectedException(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', zones=0,
                                   zone_records=99999)
