# Copyright (C) 2014 Red Hat, Inc.
#
# Author: Rich Megginson <rmeggins@redhat.com>
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
import fixtures
from oslotest import mockpatch
from requests.auth import AuthBase

from designate import tests
from designate import utils
from designate.tests.test_backend import BackendTestMixin
from designate.openstack.common import jsonutils as json
from designate.backend import impl_ipa


ipamethods = {"dnszone_add": {}, "dnszone_mod": {},
              "dnszone_del": {}, "dnsrecord_add": {},
              "dnsrecord_mod": {}, "dnsrecord_del": {},
              }


class MockIPAAuth(AuthBase):
    def __init__(self, hostname, keytab):
        self.count = 0

    def refresh_auth(self):
        self.count += 1


class MockResponse(object):
    def __init__(self, status_code, jsontext):
        self.status_code = status_code
        self.text = jsontext


class MockRequest(object):
    def __init__(self, testcase):
        self.headers = {}
        self.myauth = MockIPAAuth("ignore", "ignore")
        self.testcase = testcase
        self.error = None
        self.needauth = False

    @property
    def auth(self):
        # always return the mock object
        return self.myauth

    @auth.setter
    def auth(self, val):
        # disallow setting
        pass

    def post(self, jsonurl, data):
        # convert json data string to dict
        ddict = json.loads(data)
        # check basic parameters
        self.testcase.assertIn('method', ddict)
        meth = ddict['method']
        self.testcase.assertIn(meth, ipamethods)
        self.testcase.assertIn('params', ddict)
        self.testcase.assertIsInstance(ddict['params'], list)
        self.testcase.assertEqual(len(ddict['params']), 2)
        self.testcase.assertIsInstance(ddict['params'][0], list)
        self.testcase.assertIsInstance(ddict['params'][1], dict)
        self.testcase.assertIn('version', ddict['params'][1])
        # check method specific parameters
        if meth.startswith('dnsrecord_'):
            self.testcase.assertEqual(len(ddict['params'][0]), 2)
            # domain params end with a .
            param1 = ddict['params'][0][0]
            self.testcase.assertEqual(param1[-1], ".")
        elif meth.startswith('dnszone_'):
            self.testcase.assertEqual(len(ddict['params'][0]), 1)
            param1 = ddict['params'][0][0]
            self.testcase.assertEqual(param1[-1], ".")

        rc = {}
        if self.needauth:
            self.needauth = False  # reset
            return MockResponse(401, json.dumps(rc))
        if self.error:
            rc['error'] = {'code': self.error}
            self.error = None  # reset
        else:
            rc['error'] = None
        return MockResponse(200, json.dumps(rc))


class IPABackendTestCase(tests.TestCase, BackendTestMixin):

    def get_record_fixture(self, recordset_type, fixture=0, values=None):
        """override to ensure all records have a recordset_id"""
        values = values or {}

        return super(IPABackendTestCase, self).get_record_fixture(
            recordset_type, fixture,
            values={
                'recordset_id': utils.generate_uuid()
            }
        )

    def setUp(self):
        super(IPABackendTestCase, self).setUp()
        self.request = MockRequest(self)
        # make requests return our mock object

        def getSession():
            return self.request

        # replace requests.Session() with our mock version
        self.useFixture(fixtures.MonkeyPatch('requests.Session', getSession))

        self.config(backend_driver='ipa', group='service:agent')
        self.backend = self.get_backend_driver()
        self.CONF['backend:ipa'].ipa_auth_driver_class = \
            "designate.tests.test_backend.test_ipa.MockIPAAuth"
        self.backend.start()

        # Since some CRUD methods in impl_ipa call central's find_servers
        # and find_records method, mock it up to return our fixture.
        self.useFixture(mockpatch.PatchObject(
            self.backend.central_service,
            'find_servers',
            return_value=[self.get_server_fixture()]
        ))

        self.useFixture(mockpatch.PatchObject(
            self.backend.central_service,
            'find_records',
            return_value=[self.get_record_fixture('A')]
        ))

    def test_create_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)

    def test_update_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        self.backend.update_server(context, server)

    def test_delete_server(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        self.backend.delete_server(context, server)

    def test_create_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.backend.create_domain(context, domain)

    def test_update_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.backend.create_domain(context, domain)
        domain['serial'] = 123456789
        self.backend.update_domain(context, domain)

    def test_delete_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.backend.create_domain(context, domain)
        self.backend.delete_domain(context, domain)

    def test_create_domain_dup_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.request.error = impl_ipa.IPA_DUPLICATE
        self.assertRaises(impl_ipa.IPADuplicateDomain,
                          self.backend.create_domain,
                          context, domain)
        self.assertIsNone(self.request.error)

    def test_update_domain_error_no_domain(self):
        context = self.get_context()
        server = self.get_server_fixture()
        domain = self.get_domain_fixture()
        self.backend.create_server(context, server)
        self.backend.create_domain(context, domain)
        self.request.error = impl_ipa.IPA_NOT_FOUND
        self.assertRaises(impl_ipa.IPADomainNotFound,
                          self.backend.update_domain,
                          context, domain)

    def test_create_record(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        recordset = self.get_recordset_fixture(domain['name'], "A")
        record = self.get_record_fixture("A")
        self.backend.create_record(context, domain, recordset, record)
        self.backend.delete_domain(context, domain)

    def test_create_record_error_no_changes(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        recordset = self.get_recordset_fixture(domain['name'], "A")
        record = self.get_record_fixture("A")
        self.request.error = impl_ipa.IPA_NO_CHANGES
        # backend should ignore this error
        self.backend.create_record(context, domain, recordset, record)
        self.assertIsNone(self.request.error)
        self.backend.delete_domain(context, domain)

    def test_create_domain_error_no_changes(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.request.error = impl_ipa.IPA_NO_CHANGES
        # backend should ignore this error
        self.backend.create_domain(context, domain)
        self.assertIsNone(self.request.error)
        self.backend.delete_domain(context, domain)

    def test_create_record_error_dup_record(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        recordset = self.get_recordset_fixture(domain['name'], "A")
        record = self.get_record_fixture("A")
        self.request.error = impl_ipa.IPA_DUPLICATE  # causes request to raise
        self.assertRaises(impl_ipa.IPADuplicateRecord,
                          self.backend.create_record,
                          context, domain, recordset, record)
        self.assertIsNone(self.request.error)
        self.backend.delete_domain(context, domain)

    def test_update_record_error_no_record(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        recordset = self.get_recordset_fixture(domain['name'], "A")
        record = self.get_record_fixture("A")
        self.request.error = impl_ipa.IPA_NOT_FOUND  # causes request to raise
        self.assertRaises(impl_ipa.IPARecordNotFound,
                          self.backend.update_record,
                          context, domain, recordset, record)
        self.assertIsNone(self.request.error)
        self.backend.delete_domain(context, domain)

    def test_update_record_unknown_error(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        recordset = self.get_recordset_fixture(domain['name'], "A")
        record = self.get_record_fixture("A")
        self.request.error = 1234  # causes request to raise
        self.assertRaises(impl_ipa.IPAUnknownError, self.backend.update_record,
                          context, domain, recordset, record)
        self.assertIsNone(self.request.error)
        self.backend.delete_domain(context, domain)

    def test_create_record_reauth(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        recordset = self.get_recordset_fixture(domain['name'], "A")
        record = self.get_record_fixture("A")
        self.request.needauth = True  # causes request to reauth
        beforecount = self.request.myauth.count
        self.backend.create_record(context, domain, recordset, record)
        self.assertFalse(self.request.needauth)
        self.assertEqual(self.request.myauth.count, (beforecount + 1))
        self.backend.delete_domain(context, domain)

    def test_create_record_reauth_fail(self):
        context = self.get_context()
        server = self.get_server_fixture()
        self.backend.create_server(context, server)
        domain = self.get_domain_fixture()
        self.backend.create_domain(context, domain)
        recordset = self.get_recordset_fixture(domain['name'], "A")
        record = self.get_record_fixture("A")
        self.request.needauth = True  # causes request to reauth
        self.backend.ntries = 0  # force exception upon retry
        self.assertRaises(impl_ipa.IPACommunicationFailure,
                          self.backend.create_record, context, domain,
                          recordset, record)
        self.assertFalse(self.request.needauth)
        self.assertNotEqual(self.backend.ntries, 0)
        self.backend.delete_domain(context, domain)
