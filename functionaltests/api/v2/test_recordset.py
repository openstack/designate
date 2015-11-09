"""
Copyright 2015 Rackspace

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
import dns.rdatatype
from tempest_lib import exceptions

from functionaltests.common import datagen
from functionaltests.common import dnsclient
from functionaltests.common import utils
from functionaltests.api.v2.base import DesignateV2Test
from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.fixtures import ZoneFixture
from functionaltests.api.v2.fixtures import RecordsetFixture


RECORDSETS_DATASET = {
    'A': dict(
        make_recordset=lambda z: datagen.random_a_recordset(z.name)),
    'AAAA': dict(
        make_recordset=lambda z: datagen.random_aaaa_recordset(z.name)),
    'CNAME': dict(
        make_recordset=lambda z: datagen.random_cname_recordset(z.name)),
    'MX': dict(
        make_recordset=lambda z: datagen.random_mx_recordset(z.name)),
    'SPF': dict(
        make_recordset=lambda z: datagen.random_spf_recordset(z.name)),
    'SRV': dict(
        make_recordset=lambda z: datagen.random_srv_recordset(z.name)),
    'SSHFP': dict(
        make_recordset=lambda z: datagen.random_sshfp_recordset(z.name)),
    'TXT': dict(
        make_recordset=lambda z: datagen.random_txt_recordset(z.name)),
}

WILDCARD_RECORDSETS_DATASET = {
    'A': dict(make_recordset=lambda z:
        datagen.random_a_recordset(zone_name=z.name,
                                   name="*.{0}".format(z.name))),
    'AAAA': dict(make_recordset=lambda z:
        datagen.random_aaaa_recordset(zone_name=z.name,
                                      name="*.{0}".format(z.name))),
    'CNAME': dict(make_recordset=lambda z:
        datagen.random_cname_recordset(zone_name=z.name,
                                       name="*.{0}".format(z.name))),
    'MX': dict(make_recordset=lambda z:
        datagen.random_mx_recordset(zone_name=z.name,
                                    name="*.{0}".format(z.name))),
    'SPF': dict(make_recordset=lambda z:
        datagen.random_spf_recordset(zone_name=z.name,
                                     name="*.{0}".format(z.name))),
    'SSHFP': dict(make_recordset=lambda z:
        datagen.random_sshfp_recordset(zone_name=z.name,
                                       name="*.{0}".format(z.name))),
    'TXT': dict(make_recordset=lambda z:
        datagen.random_txt_recordset(zone_name=z.name,
                                     name="*.{0}".format(z.name))),
}


@utils.parameterized_class
class RecordsetTest(DesignateV2Test):

    def setUp(self):
        super(RecordsetTest, self).setUp()
        self.increase_quotas(user='default')
        self.ensure_tld_exists('com')
        self.zone = self.useFixture(ZoneFixture()).created_zone

    def test_list_recordsets(self):
        post_model = datagen.random_a_recordset(self.zone.name)
        self.useFixture(RecordsetFixture(self.zone.id, post_model))
        resp, model = RecordsetClient.as_user('default') \
            .list_recordsets(self.zone.id)
        self.assertEqual(200, resp.status)
        self.assertGreater(len(model.recordsets), 0)

    def assert_dns(self, model):
        results = dnsclient.query_servers(model.name, model.type)

        model_data = model.to_dict()
        if model.type == 'AAAA':
            model_data['records'] = utils.shorten_ipv6_addrs(
                model_data['records'])

        for answer in results:
            data = {
                "type": dns.rdatatype.to_text(answer.rdtype),
                "name": str(answer.canonical_name),
                # DNSPython wraps TXT values in "" so '+all v=foo' becomes
                # '"+all" "+v=foo"'
                "records": [i.to_text().replace('"', '')
                            for i in answer.rrset.items]
            }

            if answer.rrset.ttl != 0:
                data['ttl'] = answer.rrset.ttl

            self.assertEqual(model_data, data)

    @utils.parameterized(RECORDSETS_DATASET)
    def test_crud_recordset(self, make_recordset):
        post_model = make_recordset(self.zone)
        fixture = self.useFixture(RecordsetFixture(self.zone.id, post_model))
        recordset_id = fixture.created_recordset.id

        self.assert_dns(fixture.post_model)

        put_model = make_recordset(self.zone)
        del put_model.name  # don't try to update the name
        resp, put_resp_model = RecordsetClient.as_user('default') \
            .put_recordset(self.zone.id, recordset_id, put_model)
        self.assertEqual(202, resp.status, "on put response")
        self.assertEqual("PENDING", put_resp_model.status)
        self.assertEqual(post_model.name, put_resp_model.name)
        self.assertEqual(put_model.records, put_resp_model.records)
        self.assertEqual(put_model.ttl, put_resp_model.ttl)

        RecordsetClient.as_user('default').wait_for_recordset(
            self.zone.id, recordset_id)

        put_model.name = post_model.name
        self.assert_dns(put_model)

        resp, delete_resp_model = RecordsetClient.as_user('default') \
            .delete_recordset(self.zone.id, recordset_id)
        self.assertEqual(202, resp.status, "on delete response")
        RecordsetClient.as_user('default').wait_for_404(
            self.zone.id, recordset_id)

    @utils.parameterized(RECORDSETS_DATASET)
    def test_create_invalid(self, make_recordset, data=None):
        data = data or ["b0rk"]

        client = RecordsetClient.as_user('default')

        for i in data:
            model = make_recordset(self.zone)
            model.data = i
            self._assert_exception(
                exceptions.BadRequest, 'invalid_object', 400,
                client.post_recordset, self.zone.id, model)

    @utils.parameterized(RECORDSETS_DATASET)
    def test_update_invalid(self, make_recordset, data=None):
        data = data or ["b0rk"]

        post_model = make_recordset(self.zone)
        fixture = self.useFixture(RecordsetFixture(self.zone.id, post_model))
        recordset_id = fixture.created_recordset.id

        client = RecordsetClient.as_user('default')
        for i in data:
            model = make_recordset(self.zone)
            model.data = i
            self._assert_exception(
                exceptions.BadRequest, 'invalid_object', 400,
                client.put_recordset, self.zone.id, recordset_id, model)

    @utils.parameterized(WILDCARD_RECORDSETS_DATASET)
    def test_can_create_and_query_wildcard_recordset(self, make_recordset):
        post_model = make_recordset(self.zone)
        self.useFixture(RecordsetFixture(self.zone.id, post_model))

        verify_models = [
            post_model.from_dict(post_model.to_dict()) for x in range(3)
        ]
        verify_models[0].name = "abc.{0}".format(self.zone.name)
        verify_models[1].name = "abc.def.{0}".format(self.zone.name)
        verify_models[2].name = "abc.def.hij.{0}".format(self.zone.name)

        for m in verify_models:
            self.assert_dns(m)

    def test_cname_recordsets_cannot_have_more_than_one_record(self):
        post_model = datagen.random_cname_recordset(zone_name=self.zone.name)
        post_model.records = [
            "a.{0}".format(self.zone.name),
            "b.{0}".format(self.zone.name),
        ]

        client = RecordsetClient.as_user('default')
        self.assertRaises(exceptions.BadRequest,
            client.post_recordset, self.zone.id, post_model)


class RecordsetOwnershipTest(DesignateV2Test):

    def setUp(self):
        super(RecordsetOwnershipTest, self).setUp()
        self.increase_quotas(user='default')
        self.increase_quotas(user='alt')
        self.ensure_tld_exists('com')

    def test_no_create_recordset_by_alt_tenant(self):
        zone = self.useFixture(ZoneFixture(user='default')).created_zone

        # try with name=A123456.zone.com.
        recordset = datagen.random_a_recordset(zone_name=zone.name)
        self.assertRaises(exceptions.RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(zone.id, recordset))

        # try with name=zone.com.
        recordset.name = zone.name
        self.assertRaises(exceptions.RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(zone.id, recordset))

    def test_no_create_super_recordsets(self):
        # default creates zone a.b.c.example.com.
        # alt fails to create record with name b.c.example.com
        zone_data = datagen.random_zone_data()
        recordset = datagen.random_a_recordset(zone_name=zone_data.name)
        recordset.name = 'b.c.' + zone_data.name
        zone_data.name = 'a.b.c.' + zone_data.name

        fixture = self.useFixture(ZoneFixture(zone_data, user='default'))
        self.assertRaises(exceptions.RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(fixture.created_zone.id, recordset))

    def test_no_create_recordset_via_alt_domain(self):
        zone = self.useFixture(ZoneFixture(user='default')).created_zone
        alt_zone = self.useFixture(ZoneFixture(user='alt')).created_zone

        # alt attempts to create record with name A12345.{zone}
        recordset = datagen.random_a_recordset(zone_name=zone.name)
        self.assertRaises(exceptions.RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(zone.id, recordset))
        self.assertRaises(exceptions.RestClientException,
            lambda: RecordsetClient.as_user('alt')
                    .post_recordset(alt_zone.id, recordset))
