# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from designate.openstack.common import cfg
from designate.openstack.common import log as logging
from designate.tests import TestCase
from designate import quota
from designate import exceptions

LOG = logging.getLogger(__name__)


class QuotaTestCase(TestCase):
    __test__ = False

    def setUp(self):
        super(QuotaTestCase, self).setUp()
        self.quota = quota.get_quota()

    def test_get_tenant_quotas(self):
        context = self.get_admin_context()

        quotas = self.quota.get_tenant_quotas(context, 'DefaultQuotaTenant')

        self.assertIsNotNone(quotas)
        self.assertEqual(quotas, {
            'domains': cfg.CONF.quota_domains,
            'domain_records': cfg.CONF.quota_domain_records
        })

    def test_limit_check_unknown(self):
        context = self.get_admin_context()

        with self.assertRaises(exceptions.QuotaResourceUnknown):
            self.quota.limit_check(context, 'tenant_id', unknown=0)

        with self.assertRaises(exceptions.QuotaResourceUnknown):
            self.quota.limit_check(context, 'tenant_id', unknown=0, domains=0)

    def test_limit_check_under(self):
        context = self.get_admin_context()

        self.quota.limit_check(context, 'tenant_id', domains=0)
        self.quota.limit_check(context, 'tenant_id', domain_records=0)
        self.quota.limit_check(context, 'tenant_id', domains=0,
                               domain_records=0)

        self.quota.limit_check(context, 'tenant_id',
                               domains=(cfg.CONF.quota_domains - 1))
        self.quota.limit_check(
            context,
            'tenant_id',
            domain_records=(cfg.CONF.quota_domain_records - 1))

    def test_limit_check_at(self):
        context = self.get_admin_context()

        with self.assertRaises(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id',
                                   domains=cfg.CONF.quota_domains)

        with self.assertRaises(exceptions.OverQuota):
            self.quota.limit_check(
                context,
                'tenant_id',
                domain_records=cfg.CONF.quota_domain_records)

    def test_limit_check_over(self):
        context = self.get_admin_context()

        with self.assertRaises(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', domains=99999)

        with self.assertRaises(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', domain_records=99999)

        with self.assertRaises(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', domains=99999,
                                   domain_records=99999)

        with self.assertRaises(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', domains=99999,
                                   domain_records=0)

        with self.assertRaises(exceptions.OverQuota):
            self.quota.limit_check(context, 'tenant_id', domains=0,
                                   domain_records=99999)
