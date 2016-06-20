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

    def test_list_recordsets_with_filtering(self):
        # This test ensures the behavior in bug #1561746 won't happen
        post_model = datagen.random_a_recordset(self.zone.name,
                                                ip='192.168.1.2')
        self.useFixture(RecordsetFixture(self.zone.id, post_model))
        for i in range(1, 3):
            post_model = datagen.random_a_recordset(self.zone.name,
                                                    ip='10.0.1.{}'.format(i))
            self.useFixture(RecordsetFixture(self.zone.id, post_model))

        # Add limit in filter to make response paginated
        filters = {"data": "10.*", "limit": 2}
        resp, model = RecordsetClient.as_user('default') \
            .list_recordsets(self.zone.id, filters=filters)
        self.assertEqual(200, resp.status)
        self.assertEqual(2, model.metadata.total_count)
        self.assertEqual(len(model.recordsets), 2)
        self.assertIsNotNone(model.links.next)

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
