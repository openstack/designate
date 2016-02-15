"""
Copyright 2016 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from tempest_lib import exceptions

from functionaltests.common import datagen
from functionaltests.common import utils
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.fixtures import ZoneFixture
from functionaltests.api.v2.fixtures import RecordsetFixture
from functionaltests.api.v2.test_recordset import RECORDSETS_DATASET


INVALID_TXT_DATASET = {
    'trailing_slash': dict(data='\\'),
    'trailing_double_slash': dict(data='\\\\'),
    'trailing_slash_after_text': dict(data='v=spf1 +all\\'),
}

VALID_TXT_DATASET = {
    'slash_with_one_trailing_space': dict(data='\\ '),
    'slash_with_many_trailing_space': dict(data='\\    '),
    'text_with_slash_and_trailing_space': dict(data='the txts \   '),
}

INVALID_MX_DATASET = {
    'empty_preference': dict(pref=''),
    'minus_zero_preference': dict(pref='-0'),
    'minus_one_preference': dict(pref='-1'),
}

INVALID_SSHFP_DATASET = {
    'minus_zero_algorithm': dict(algo='-0', finger=None),
    'minus_zero_fingerprint': dict(algo=None, finger='-0'),
    'minus_one_algorithm': dict(algo='-1', finger=None),
    'minus_one_fingerprint': dict(algo=None, finger='-1'),
}


@utils.parameterized_class
class RecordsetValidationTest(DesignateV2Test):

    def setUp(self):
        super(RecordsetValidationTest, self).setUp()
        self.increase_quotas(user='default')
        self.ensure_tld_exists('com')
        self.zone = self.useFixture(ZoneFixture()).created_zone
        self.client = RecordsetClient.as_user('default')

    @utils.parameterized(RECORDSETS_DATASET)
    def test_create_invalid(self, make_recordset, data=None):
        data = data or ["b0rk"]

        for i in data:
            model = make_recordset(self.zone)
            model.data = i
            self._assert_exception(
                exceptions.BadRequest, 'invalid_object', 400,
                self.client.post_recordset, self.zone.id, model)

    @utils.parameterized(RECORDSETS_DATASET)
    def test_update_invalid(self, make_recordset, data=None):
        data = data or ["b0rk"]

        post_model = make_recordset(self.zone)
        fixture = self.useFixture(RecordsetFixture(self.zone.id, post_model))
        recordset_id = fixture.created_recordset.id

        for i in data:
            model = make_recordset(self.zone)
            model.data = i
            self._assert_exception(
                exceptions.BadRequest, 'invalid_object', 400,
                self.client.put_recordset, self.zone.id, recordset_id, model)

    def test_cannot_create_wildcard_NS_recordset(self):
        model = datagen.wildcard_ns_recordset(self.zone.name)
        self._assert_exception(
            exceptions.BadRequest, 'invalid_object', 400,
            self.client.post_recordset, self.zone.id, model)

    def test_cname_recordsets_cannot_have_more_than_one_record(self):
        post_model = datagen.random_cname_recordset(zone_name=self.zone.name)
        post_model.records = [
            "a.{0}".format(self.zone.name),
            "b.{0}".format(self.zone.name),
        ]

        self.assertRaises(exceptions.BadRequest,
            self.client.post_recordset, self.zone.id, post_model)

    @utils.parameterized(INVALID_TXT_DATASET)
    def test_cannot_create_TXT_with(self, data):
        post_model = datagen.random_txt_recordset(self.zone.name, data)
        e = self._assert_exception(
            exceptions.BadRequest, 'invalid_object', 400,
            self.client.post_recordset, self.zone.id, post_model,
        )
        self.assertEqual(
            "u'%s' is not a 'txt-data'" % data.replace('\\', '\\\\'),
            e.resp_body['errors']['errors'][0]['message'],
        )

    @utils.parameterized(VALID_TXT_DATASET)
    def test_create_TXT_with(self, data):
        post_model = datagen.random_txt_recordset(self.zone.name, data)
        fixture = self.useFixture(RecordsetFixture(self.zone.id, post_model))
        recordset = fixture.created_recordset
        self.client.wait_for_recordset(self.zone.id, recordset.id)

    @utils.parameterized(VALID_TXT_DATASET)
    def test_create_SPF_with(self, data):
        post_model = datagen.random_spf_recordset(self.zone.name, data)
        fixture = self.useFixture(RecordsetFixture(self.zone.id, post_model))
        recordset = fixture.created_recordset
        self.client.wait_for_recordset(self.zone.id, recordset.id)

    @utils.parameterized(INVALID_MX_DATASET)
    def test_cannot_create_MX_with(self, pref):
        post_model = datagen.random_mx_recordset(self.zone.name, pref=pref)
        self._assert_exception(
            exceptions.BadRequest, 'invalid_object', 400,
            self.client.post_recordset, self.zone.id, post_model,
        )

    @utils.parameterized(INVALID_SSHFP_DATASET)
    def test_cannot_create_SSHFP_with(self, algo, finger):
        post_model = datagen.random_sshfp_recordset(
            zone_name=self.zone.name,
            algorithm_number=algo,
            fingerprint_type=finger,
        )
        self._assert_exception(
            exceptions.BadRequest, 'invalid_object', 400,
            self.client.post_recordset, self.zone.id, post_model,
        )
