# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
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

from tempest.api.dns import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class RecordsTest(base.BaseDnsTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(RecordsTest, cls).setUpClass()
        cls.client = cls.dns_records_client
        # Creates domains and Records for testcase
        cls.setup_records = list()
        name = data_utils.rand_name('domain') + '.com.'
        email = data_utils.rand_name('dns') + '@testmail.com'
        _, cls.domain = cls.dns_domains_client.create_domain(name, email)
        # Creates a record with type as A
        r_name = 'www.' + name
        data1 = "192.0.2.3"
        _, record = cls.client.create_record(
            domain_id=cls.domain['id'], name=r_name, data=data1,
            type='A')
        cls.setup_records.append(record)
        # Creates a record with type AAAA
        data2 = "2001:db8:0:1234:0:5678:9:12"
        _, record = cls.client.create_record(
            domain_id=cls.domain['id'], name=r_name,
            data=data2, type='AAAA')
        cls.setup_records.append(record)

    @classmethod
    def tearDownClass(cls):
        for record in cls.setup_records:
            cls.client.delete_record(cls.domain['id'], record['id'])
        cls.dns_domains_client.delete_domain(cls.domain['id'])

    def _delete_record(self, domain_id, record_id):
        self.client.delete_record(domain_id, record_id)
        self.assertRaises(exceptions.NotFound,
                          self.client.get_record, domain_id, record_id)

    @test.attr(type='gate')
    def test_list_records_for_domain(self):
        # Get a list of records for a domain
        _, records = self.client.list_records(self.domain['id'])
        # Verify records created in setup class are in the list
        for record in self.setup_records:
            self.assertIn(record['id'], map(lambda x: x['id'], records))

    @test.attr(type='smoke')
    def test_create_update_get_delete_record(self):
        # Create Domain
        name = data_utils.rand_name('domain') + '.com.'
        email = data_utils.rand_name('dns') + '@testmail.com'
        _, domain = self.dns_domains_client.create_domain(name, email)
        self.addCleanup(self.dns_domains_client.delete_domain, domain['id'])
        # Create Record
        r_name = 'www.' + name
        r_data = "192.0.2.4"
        _, record = self.client.create_record(domain_id=domain['id'],
                                              name=r_name, data=r_data,
                                              type='A')
        self.addCleanup(self._delete_record, domain['id'], record['id'])
        self.assertIsNotNone(record['id'])
        self.assertEqual(domain['id'], record['domain_id'])
        self.assertEqual(r_name, record['name'])
        self.assertEqual(r_data, record['data'])
        self.assertEqual('A', record['type'])
        # Update Record with data and ttl
        r_data1 = "192.0.2.5"
        r_ttl = 3600
        _, update_record = self.client.update_record(domain_id=domain['id'],
                                                     record_id=record['id'],
                                                     name=r_name, type='A',
                                                     data=r_data1, ttl=r_ttl)
        self.assertEqual(r_data1, update_record['data'])
        self.assertEqual(r_ttl, update_record['ttl'])
        # GET record
        _, get_record = self.client.get_record(domain_id=domain['id'],
                                               record_id=record['id'])
        self.assertEqual(update_record['data'], get_record['data'])
        self.assertEqual(update_record['name'], get_record['name'])
        self.assertEqual(update_record['type'], get_record['type'])
        self.assertEqual(update_record['ttl'], get_record['ttl'])
        self.assertEqual(update_record['domain_id'], get_record['domain_id'])
