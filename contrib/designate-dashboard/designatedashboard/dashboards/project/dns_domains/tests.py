# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import unicode_literals

from django.core.urlresolvers import reverse  # noqa
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from designatedashboard.dashboards.project.dns_domains import forms


DOMAIN_ID = '123'
INDEX_URL = reverse('horizon:project:dns_domains:index')
RECORDS_URL = reverse('horizon:project:dns_domains:records', args=[DOMAIN_ID])


class DNSDomainsTests(test.TestCase):

    def setUp(self):
        super(DNSDomainsTests, self).setUp()

    @test.create_stubs(
        {api.designate: ('domain_list',)})
    def test_index(self):
        domains = self.dns_domains.list()
        api.designate.domain_list(
            IsA(http.HttpRequest)).AndReturn(domains)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/dns_domains/index.html')
        self.assertEqual(len(res.context['table'].data), len(domains))

    @test.create_stubs(
        {api.designate: ('domain_get', 'server_list', 'record_list')})
    def test_records(self):
        domain_id = '123'
        domain = self.dns_domains.first()
        servers = self.dns_servers.list()
        records = self.dns_records.list()

        api.designate.domain_get(
            IsA(http.HttpRequest),
            domain_id).AndReturn(domain)

        api.designate.server_list(
            IsA(http.HttpRequest),
            domain_id).AndReturn(servers)

        api.designate.record_list(
            IsA(http.HttpRequest),
            domain_id).AndReturn(records)

        self.mox.ReplayAll()

        res = self.client.get(RECORDS_URL)

        self.assertTemplateUsed(res, 'project/dns_domains/records.html')
        self.assertEqual(len(res.context['table'].data), len(records))


class BaseRecordFormCleanTests(test.TestCase):

    DOMAIN_NAME = 'foo.com.'
    HOSTNAME = 'www.foo.com.'

    MSG_FIELD_REQUIRED = 'This field is required'
    MSG_INVALID_HOSTNAME = 'Enter a valid hostname'
    MSG_OUTSIDE_DOMAIN = 'Name must be in the current domain'

    def setUp(self):
        super(BaseRecordFormCleanTests, self).setUp()

        # Request object with messages support
        self.request = self.factory.get('', {})

        # Set-up form instance
        self.form = forms.RecordCreate(self.request)
        self.form._errors = {}
        self.form.cleaned_data = {
            'domain_name': self.DOMAIN_NAME,
            'name': '',
            'data': '',
            'txt': '',
            'priority': None,
            'ttl': None,
        }

    def assert_no_errors(self):
        self.assertEqual(self.form._errors, {})

    def assert_error(self, field, msg):
        self.assertIn(msg, self.form._errors[field])

    def assert_required_error(self, field):
        self.assert_error(field, self.MSG_FIELD_REQUIRED)


class ARecordFormTests(BaseRecordFormCleanTests):

    IPV4 = '1.1.1.1'

    MSG_INVALID_IPV4 = 'Enter a valid IPv4 address'

    def setUp(self):
        super(ARecordFormTests, self).setUp()
        self.form.cleaned_data['type'] = 'A'
        self.form.cleaned_data['name'] = self.HOSTNAME
        self.form.cleaned_data['data'] = self.IPV4

    def test_valid_field_values(self):
        self.form.clean()
        self.assert_no_errors()

    def test_valid_name_field_wild_card(self):
        self.form.cleaned_data['name'] = '*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_no_errors()

    def test_missing_name_field(self):
        self.form.cleaned_data['name'] = ''
        self.form.clean()
        self.assert_required_error('name')

    def test_missing_data_field(self):
        self.form.cleaned_data['data'] = ''
        self.form.clean()
        self.assert_required_error('data')

    def test_invalid_name_field(self):
        self.form.cleaned_data['name'] = 'foo'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_starting_dash(self):
        self.form.cleaned_data['name'] = '-ww.foo.com'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_trailing_dash(self):
        self.form.cleaned_data['name'] = 'www.foo.co-'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_bad_wild_card(self):
        self.form.cleaned_data['name'] = 'derp.*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_outside_of_domain_name_field(self):
        self.form.cleaned_data['name'] = 'www.bar.com.'
        self.form.clean()
        self.assert_error('name', self.MSG_OUTSIDE_DOMAIN)

    def test_invalid_data_field(self):
        self.form.cleaned_data['data'] = 'foo'
        self.form.clean()
        self.assert_error('data', self.MSG_INVALID_IPV4)


class AAAARecordFormTests(BaseRecordFormCleanTests):

    IPV6 = '1111:1111:1111:11::1'

    MSG_INVALID_IPV6 = 'Enter a valid IPv6 address'

    def setUp(self):
        super(AAAARecordFormTests, self).setUp()
        self.form.cleaned_data['type'] = 'AAAA'
        self.form.cleaned_data['name'] = self.HOSTNAME
        self.form.cleaned_data['data'] = self.IPV6

    def test_valid_field_values(self):
        self.form.clean()
        self.assert_no_errors()

    def test_valid_name_field_wild_card(self):
        self.form.cleaned_data['name'] = '*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_no_errors()

    def test_missing_name_field(self):
        self.form.cleaned_data['name'] = ''
        self.form.clean()
        self.assert_required_error('name')

    def test_missing_data_field(self):
        self.form.cleaned_data['data'] = ''
        self.form.clean()
        self.assert_required_error('data')

    def test_invalid_name_field(self):
        self.form.cleaned_data['name'] = 'foo'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_starting_dash(self):
        self.form.cleaned_data['name'] = '-ww.foo.com'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_trailing_dash(self):
        self.form.cleaned_data['name'] = 'www.foo.co-'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_bad_wild_card(self):
        self.form.cleaned_data['name'] = 'derp.*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_outside_of_domain_name_field(self):
        self.form.cleaned_data['name'] = 'www.bar.com.'
        self.form.clean()
        self.assert_error('name', self.MSG_OUTSIDE_DOMAIN)

    def test_invalid_data_field(self):
        self.form.cleaned_data['data'] = 'foo'
        self.form.clean()
        self.assert_error('data', self.MSG_INVALID_IPV6)


class CNAMERecordFormTests(BaseRecordFormCleanTests):

    CNAME = 'bar.foo.com.'

    def setUp(self):
        super(CNAMERecordFormTests, self).setUp()
        self.form.cleaned_data['type'] = 'CNAME'
        self.form.cleaned_data['name'] = self.HOSTNAME
        self.form.cleaned_data['data'] = self.CNAME

    def test_valid_field_values(self):
        self.form.clean()
        self.assert_no_errors()

    def test_valid_name_field_wild_card(self):
        self.form.cleaned_data['name'] = '*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_no_errors()

    def test_missing_name_field(self):
        self.form.cleaned_data['name'] = ''
        self.form.clean()
        self.assert_required_error('name')

    def test_missing_data_field(self):
        self.form.cleaned_data['data'] = ''
        self.form.clean()
        self.assert_required_error('data')

    def test_invalid_name_field(self):
        self.form.cleaned_data['name'] = 'foo'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_starting_dash(self):
        self.form.cleaned_data['name'] = '-ww.foo.com'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_trailing_dash(self):
        self.form.cleaned_data['name'] = 'www.foo.co-'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_bad_wild_card(self):
        self.form.cleaned_data['name'] = 'derp.*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_outside_of_domain_name_field(self):
        self.form.cleaned_data['name'] = 'www.bar.com.'
        self.form.clean()
        self.assert_error('name', self.MSG_OUTSIDE_DOMAIN)

    def test_invalid_data_field(self):
        self.form.cleaned_data['data'] = 'foo'
        self.form.clean()
        self.assert_error('data', self.MSG_INVALID_HOSTNAME)


class MXRecordFormTests(BaseRecordFormCleanTests):

    MAIL_SERVER = 'mail.foo.com.'
    PRIORITY = 10

    def setUp(self):
        super(MXRecordFormTests, self).setUp()
        self.form.cleaned_data['type'] = 'MX'
        self.form.cleaned_data['data'] = self.MAIL_SERVER
        self.form.cleaned_data['priority'] = self.PRIORITY

    def test_valid_field_values(self):
        self.form.clean()
        self.assert_no_errors()

    def test_missing_data_field(self):
        self.form.cleaned_data['data'] = ''
        self.form.clean()
        self.assert_required_error('data')

    def test_missing_priority_field(self):
        self.form.cleaned_data['priority'] = None
        self.form.clean()
        self.assert_required_error('priority')

    def test_invalid_data_field(self):
        self.form.cleaned_data['data'] = 'foo'
        self.form.clean()
        self.assert_error('data', self.MSG_INVALID_HOSTNAME)

    def test_default_assignment_name_field(self):
        self.form.clean()
        self.assertEqual(self.DOMAIN_NAME, self.form.cleaned_data['name'])


class TXTRecordFormTests(BaseRecordFormCleanTests):

    TEXT = 'Lorem ipsum'

    def setUp(self):
        super(TXTRecordFormTests, self).setUp()
        self.form.cleaned_data['type'] = 'TXT'
        self.form.cleaned_data['name'] = self.HOSTNAME
        self.form.cleaned_data['txt'] = self.TEXT

    def test_valid_field_values(self):
        self.form.clean()
        self.assert_no_errors()

    def test_valid_name_field_wild_card(self):
        self.form.cleaned_data['name'] = '*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_no_errors()

    def test_missing_name_field(self):
        self.form.cleaned_data['name'] = ''
        self.form.clean()
        self.assert_required_error('name')

    def test_missing_txt_field(self):
        self.form.cleaned_data['txt'] = ''
        self.form.clean()
        self.assert_required_error('txt')

    def test_invalid_name_field(self):
        self.form.cleaned_data['name'] = 'foo'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_starting_dash(self):
        self.form.cleaned_data['name'] = '-ww.foo.com'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_trailing_dash(self):
        self.form.cleaned_data['name'] = 'www.foo.co-'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_invalid_name_field_bad_wild_card(self):
        self.form.cleaned_data['name'] = 'derp.*.' + self.DOMAIN_NAME
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_HOSTNAME)

    def test_outside_of_domain_name_field(self):
        self.form.cleaned_data['name'] = 'www.bar.com.'
        self.form.clean()
        self.assert_error('name', self.MSG_OUTSIDE_DOMAIN)

    def test_default_assignment_data_field(self):
        self.form.clean()
        self.assertEqual(self.TEXT, self.form.cleaned_data['data'])


class SRVRecordFormTests(BaseRecordFormCleanTests):

    SRV_NAME = '_foo._tcp.'
    SRV_DATA = '1 1 srv.foo.com.'
    PRIORITY = 10

    MSG_INVALID_SRV_NAME = 'Enter a valid SRV name'
    MSG_INVALID_SRV_DATA = 'Enter a valid SRV record'

    def setUp(self):
        super(SRVRecordFormTests, self).setUp()
        self.form.cleaned_data['type'] = 'SRV'
        self.form.cleaned_data['name'] = self.SRV_NAME
        self.form.cleaned_data['data'] = self.SRV_DATA
        self.form.cleaned_data['priority'] = self.PRIORITY

    def test_valid_field_values(self):
        self.form.clean()
        self.assert_no_errors()

    def test_missing_name_field(self):
        self.form.cleaned_data['name'] = ''
        self.form.clean()
        self.assert_required_error('name')

    def test_missing_data_field(self):
        self.form.cleaned_data['data'] = ''
        self.form.clean()
        self.assert_required_error('data')

    def test_missing_priority_field(self):
        self.form.cleaned_data['priority'] = None
        self.form.clean()
        self.assert_required_error('priority')

    def test_invalid_name_field(self):
        self.form.cleaned_data['name'] = 'foo'
        self.form.clean()
        self.assert_error('name', self.MSG_INVALID_SRV_NAME)

    def test_invalid_data_field(self):
        self.form.cleaned_data['data'] = 'foo'
        self.form.clean()
        self.assert_error('data', self.MSG_INVALID_SRV_DATA)

    def test_default_assignment_name_field(self):
        self.form.clean()
        self.assertEqual(self.SRV_NAME + self.DOMAIN_NAME,
                         self.form.cleaned_data['name'])
