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
from unittest import mock

from oslo_log import log as logging
import testscenarios

import designate.conf
from designate import exceptions
from designate import quota
import designate.tests.functional

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)
load_tests = testscenarios.load_tests_apply_scenarios


class QuotaTestCase(designate.tests.functional.TestCase):
    scenarios = [
        ('noop', dict(quota_driver='noop')),
        ('storage', dict(quota_driver='storage'))
    ]

    def setUp(self):
        super().setUp()
        self.config(quota_driver=self.quota_driver)
        self.quota = quota.get_quota()

    def test_get_quotas(self):
        context = self.get_admin_context()

        quotas = self.quota.get_quotas(context, 'DefaultQuotaTenant')

        self.assertIsNotNone(quotas)
        self.assertEqual({
            'api_export_size': CONF.quota_api_export_size,
            'zones': CONF.quota_zones,
            'zone_recordsets': CONF.quota_zone_recordsets,
            'zone_records': CONF.quota_zone_records,
            'recordset_records': CONF.quota_recordset_records,
        }, quotas)

    def test_limit_check_unknown(self):
        context = self.get_admin_context()

        self.assertRaisesRegex(
            exceptions.QuotaResourceUnknown,
            "'unknown' is not a valid quota resource.",
            self.quota.limit_check,
            context, 'tenant_id', unknown=0
        )

        self.assertRaisesRegex(
            exceptions.QuotaResourceUnknown,
            "'unknown' is not a valid quota resource.",
            self.quota.limit_check,
            context, 'tenant_id', unknown=0, zones=0
        )

    def test_limit_check_under(self):
        context = self.get_admin_context()

        self.quota.limit_check(context, 'tenant_id', zones=0)
        self.quota.limit_check(context, 'tenant_id', zone_records=0)
        self.quota.limit_check(context, 'tenant_id', zones=0,
                               zone_records=0)

        self.quota.limit_check(context, 'tenant_id',
                               zones=(CONF.quota_zones - 1))
        self.quota.limit_check(
            context,
            'tenant_id',
            zone_records=(CONF.quota_zone_records - 1))

    def test_limit_check_at(self):
        context = self.get_admin_context()

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zones\\.',
            self.quota.limit_check,
            context, 'tenant_id', zones=CONF.quota_zones + 1
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zone_records\\.',
            self.quota.limit_check,
            context, 'tenant_id', zone_records=CONF.quota_zone_records + 1
        )

    def test_limit_check_unlimited(self):
        context = self.get_admin_context()
        self.quota.get_quotas = mock.Mock()
        ret = {
            'zones': -1,
            'zone_recordsets': -1,
            'zone_records': -1,
            'recordset_records': -1,
            'api_export_size': -1,
        }
        self.quota.get_quotas.return_value = ret
        self.quota.limit_check(context, 'tenant_id', zones=99999)
        self.quota.limit_check(context, 'tenant_id', zone_recordsets=99999)
        self.quota.limit_check(context, 'tenant_id', zone_records=99999)
        self.quota.limit_check(context, 'tenant_id', recordset_records=99999)
        self.quota.limit_check(context, 'tenant_id', api_export_size=99999)

    def test_limit_check_zero(self):
        context = self.get_admin_context()
        self.quota.get_quotas = mock.Mock()
        ret = {
            'zones': 0,
            'zone_recordsets': 0,
            'zone_records': 0,
            'recordset_records': 0,
            'api_export_size': 0,
        }
        self.quota.get_quotas.return_value = ret

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zones\\.',
            self.quota.limit_check,
            context, 'tenant_id', zones=1
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zone_recordsets\\.',
            self.quota.limit_check,
            context, 'tenant_id', zone_recordsets=1
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zone_records\\.',
            self.quota.limit_check,
            context, 'tenant_id', zone_records=1
        )

        self.assertRaisesRegex(
            exceptions.OverQuota,
            'Quota exceeded for recordset_records\\.',
            self.quota.limit_check,
            context, 'tenant_id', recordset_records=1
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for api_export_size\\.',
            self.quota.limit_check,
            context, 'tenant_id', api_export_size=1
        )

    def test_limit_check_over(self):
        context = self.get_admin_context()

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zones\\.',
            self.quota.limit_check,
            context, 'tenant_id', zones=99999
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zone_records\\.',
            self.quota.limit_check,
            context, 'tenant_id', zone_records=99999
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zones, zone_records\\.',
            self.quota.limit_check,
            context, 'tenant_id', zones=99999, zone_records=99999
        )

        self.assertRaisesRegex(
            exceptions.OverQuota,
            'Quota exceeded for zones, zone_records, zone_recordsets\\.',
            self.quota.limit_check,
            context, 'tenant_id', zones=99999, zone_records=99999,
            zone_recordsets=99999
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zones\\.',
            self.quota.limit_check,
            context, 'tenant_id', zones=99999, zone_records=0
        )

        self.assertRaisesRegex(
            exceptions.OverQuota, 'Quota exceeded for zone_records\\.',
            self.quota.limit_check,
            context, 'tenant_id', zones=0, zone_records=99999
        )
