# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
import json as json_

from requests_mock.contrib import fixture as req_fixture
import testtools

from designate import objects
from designate.backend import impl_dynect
from designate.tests.test_backend import BackendTestCase

MASTERS = ["10.0.0.1"]
CONTACT = 'jdoe@myco.biz'


LOGIN_SUCCESS = {
    "status": "success",
    "data": {
        "token": "foo",
        "version": "3.5.6"
    },
    "job_id": 1,
    "msgs": [{
        "INFO": "login: Login successful",
        "SOURCE": "BLL",
        "ERR_CD": None,
        "LVL": "INFO"}]
}

LOGOUT_SUCCESS = {
    "status": "success",
    "data": {},
    "job_id": 1345964647,
    "msgs": [
        {
            "INFO": "logout: Logout successful",
            "SOURCE": "BLL",
            "ERR_CD": None,
            "LVL": "INFO"
        }
    ]
}

INVALID_MASTER_DATA = {
    "status": "failure",
    "data": {}, "job_id": 1326038394,
    "msgs": [
        {
            "INFO": "master: IP address expected",
            "SOURCE": "DYN",
            "ERR_CD": "INVALID_DATA",
            "LVL": "ERROR"
        },
        {
            "INFO": "create: Zone not created",
            "SOURCE": "BLL",
            "ERR_CD": None,
            "LVL": "INFO"
        }
    ]
}

TARGET_EXISTS = {
    "status": "failure",
    "data": {},
    "job_id": 1345944906,
    "msgs": [
        {
            "INFO": "name: Name already exists",
            "SOURCE": "BLL",
            "ERR_CD": "TARGET_EXISTS",
            "LVL": "ERROR"
        },
        {
            "INFO": "create: You already have this zone.",
            "SOURCE": "BLL",
            "ERR_CD": None,
            "LVL": "INFO"
        }
    ]
}


ACTIVATE_SUCCESS = {
    "status": "success",
    "data": {
        "active": "L",
        "masters": MASTERS,
        "contact_nickname": CONTACT,
        "tsig_key_name": "",
        "zone": "meep.io"
    },
    "job_id": 1345944927,
    "msgs": [
        {
            "INFO": "activate: Service activated",
            "SOURCE": "BLL",
            "ERR_CD": None,
            "LVL": "INFO"
        }
    ]
}


class DynECTTestsCase(BackendTestCase):
    def setUp(self):
        super(DynECTTestsCase, self).setUp()
        self.target = objects.PoolTarget.from_dict({
            'id': '4588652b-50e7-46b9-b688-a9bad40a873e',
            'type': 'dyndns',
            'masters': [{'host': '192.0.2.1', 'port': 53}],
            'options': [
                {'key': 'username', 'value': 'example'},
                {'key': 'password', 'value': 'secret'},
                {'key': 'customer_name', 'value': 'customer'}],
        })

        self.backend = impl_dynect.DynECTBackend(self.target)
        self.requests = self.useFixture(req_fixture.Fixture())

    def stub_url(self, method, parts=None, base_url=None, json=None, **kwargs):
        if not base_url:
            base_url = 'https://api.dynect.net:443/REST'

        if json:
            kwargs['text'] = json_.dumps(json)
            headers = kwargs.setdefault('headers', {})
            headers['Content-Type'] = 'application/json'

        if parts:
            url = '/'.join([p.strip('/') for p in [base_url] + parts])
        else:
            url = base_url

        url = url.replace("/?", "?")

        return self.requests.register_uri(method, url, **kwargs)

    def _stub_login(self):
        self.stub_url('POST', ['/Session'], json=LOGIN_SUCCESS)
        self.stub_url('DELETE', ['/Session'], json=LOGIN_SUCCESS)

    def test_create_zone_raise_dynclienterror(self):
        context = self.get_context()
        zone = self.create_zone()

        self._stub_login()

        self.stub_url(
            'POST', ['/Secondary/example.com'],
            json=INVALID_MASTER_DATA,
            status_code=400)

        with testtools.ExpectedException(impl_dynect.DynClientError):
            self.backend.create_zone(context, zone)

    def test_create_zone_duplicate_updates_existing(self):
        context = self.get_context()
        zone = self.create_zone()

        self._stub_login()

        parts = ['/Secondary', '/%s' % zone['name'].rstrip('.')]

        self.stub_url(
            'POST', parts,
            json=TARGET_EXISTS,
            status_code=400)

        update = self.stub_url('PUT', parts, json=ACTIVATE_SUCCESS)

        self.backend.create_zone(context, zone)

        self.assertTrue(update.called)
