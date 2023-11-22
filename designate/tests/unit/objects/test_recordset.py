# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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
import itertools
from unittest import mock

from oslo_config import fixture as cfg_fixture
from oslo_log import log as logging
import oslotest.base


import designate.conf
from designate import exceptions
from designate import objects
from designate.objects.adapters import DesignateAdapter


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


def create_test_recordset():
    record_set = objects.RecordSet(
        id='f6a2cbd6-7f9a-4e0c-a00d-98a02aa73fc8',
        zone_id='74038683-cab1-4056-bdf8-b39bd155ff21',
        name='www.example.org.',
        type='A',
        records=objects.RecordList(objects=[
            objects.Record(data='192.0.2.1'),
            objects.Record(data='192.0.2.2'),
        ]),
        shard=0
    )
    return record_set


class RecordSetTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    def test_init(self):
        record_set = create_test_recordset()
        self.assertEqual('www.example.org.', record_set.name)
        self.assertEqual('A', record_set.type)

    def test_to_repr(self):
        record_set = create_test_recordset()
        self.assertEqual(
            "<RecordSet id:'f6a2cbd6-7f9a-4e0c-a00d-98a02aa73fc8' type:'A' "
            "name:'www.example.org.' "
            "zone_id:'74038683-cab1-4056-bdf8-b39bd155ff21' shard:'0'>",
            repr(record_set)
        )

    def test_not_managed(self):
        record_set = create_test_recordset()
        self.assertFalse(record_set.managed)

    def test_managed(self):
        record_set = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', managed=True),
                objects.Record(data='192.0.2.2'),
            ])
        )
        self.assertTrue(record_set.managed)

    def test_action(self):
        action = 'CREATE'
        record_set = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action=action),
            ])
        )
        self.assertEqual(action, record_set.action)

    def test_action_create(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='CREATE'),
            ])
        )
        self.assertEqual('CREATE', record_set.action)

    def test_action_create_plus_update(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='CREATE'),
                objects.Record(data='192.0.2.2', action='UPDATE'),
            ])
        )
        self.assertEqual('UPDATE', record_set.action)

    def test_action_delete_plus_update(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='DELETE'),
                objects.Record(data='192.0.2.2', action='UPDATE'),
            ])
        )
        self.assertEqual('UPDATE', record_set.action)

    def test_action_delete_only(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='DELETE'),
                objects.Record(data='192.0.2.2', action='DELETE'),
            ])
        )
        self.assertEqual('DELETE', record_set.action)

    def test_status_error(self):
        statuses = ('ERROR', 'PENDING', 'ACTIVE', 'DELETED')
        for s1, s2, s3, s4 in itertools.permutations(statuses):
            record_set = objects.RecordSet(
                name='www.example.org.', type='A',
                records=objects.RecordList(objects=[
                    objects.Record(data='192.0.2.1', status=s1),
                    objects.Record(data='192.0.2.2', status=s2),
                    objects.Record(data='192.0.2.3', status=s3),
                    objects.Record(data='192.0.2.4', status=s4),
                ])
            )
            self.assertEqual(record_set.status, 'ERROR')

    def test_status_pending(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2', status='PENDING'),
                objects.Record(data='192.0.2.3', status='ACTIVE'),
            ])
        )
        self.assertEqual('PENDING', record_set.status)

    def test_status_pending2(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.3', status='ACTIVE'),
                objects.Record(data='192.0.2.2', status='PENDING'),
            ])
        )
        self.assertEqual('PENDING', record_set.status)

    def test_status_active(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.3', status='ACTIVE'),
            ])
        )
        self.assertEqual('ACTIVE', record_set.status)

    def test_status_deleted(self):
        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2', status='DELETED'),
            ])
        )
        self.assertEqual('DELETED', record_set.status)

    def test_status_many_expect_error(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2', status='ACTIVE'),
                objects.Record(data='192.0.2.3', status='DELETED'),
                objects.Record(data='192.0.2.4', status='DELETED'),
                objects.Record(data='192.0.2.5', status='DELETED'),
                objects.Record(data='192.0.2.6', status='ACTIVE'),
                objects.Record(data='192.0.2.7', status='ACTIVE'),
                objects.Record(data='192.0.2.8', status='ERROR'),
                objects.Record(data='192.0.2.9', status='ACTIVE'),
                objects.Record(data='192.0.2.10', status='ACTIVE'),
            ])
        )
        self.assertEqual('ERROR', rs.status)

    def test_status_many_expect_pending(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2', status='ACTIVE'),
                objects.Record(data='192.0.2.3', status='DELETED'),
                objects.Record(data='192.0.2.4', status='PENDING'),
                objects.Record(data='192.0.2.5', status='DELETED'),
                objects.Record(data='192.0.2.6', status='PENDING'),
                objects.Record(data='192.0.2.7', status='ACTIVE'),
                objects.Record(data='192.0.2.8', status='DELETED'),
                objects.Record(data='192.0.2.9', status='PENDING'),
                objects.Record(data='192.0.2.10', status='ACTIVE'),
            ])
        )
        self.assertEqual('PENDING', rs.status)

    def test_status_many_expect_active(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2', status='ACTIVE'),
                objects.Record(data='192.0.2.3', status='DELETED'),
                objects.Record(data='192.0.2.4', status='DELETED'),
                objects.Record(data='192.0.2.5', status='DELETED'),
                objects.Record(data='192.0.2.6', status='ACTIVE'),
                objects.Record(data='192.0.2.7', status='ACTIVE'),
                objects.Record(data='192.0.2.8', status='DELETED'),
                objects.Record(data='192.0.2.9', status='ACTIVE'),
                objects.Record(data='192.0.2.10', status='ACTIVE'),
            ])
        )
        self.assertEqual('ACTIVE', rs.status)

    def test_validate(self):
        record_set = create_test_recordset()
        record_set.validate()

    def test_validate_attribute_error(self):
        record_set = objects.RecordSet(
            name='www.example.org.',
            type='NAPTR',
            records=objects.RecordList(objects=[
                objects.Record(data=None),
            ])
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            record_set.validate
        )

    def test_validate_type_error(self):
        record_set = objects.RecordSet(
            name='www.example.org.',
            type='TXT',
            records=objects.RecordList(objects=[
                objects.Record(data=None),
            ])
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            record_set.validate
        )

    def test_validate_unsupported_recordset_type(self):
        CONF.set_override('supported_record_type', ['A', 'AAAA', 'CNAME'])

        record_set = objects.RecordSet(
            name='www.example.org.', type='PTR',
            records=[]
        )
        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            record_set.validate
        )

    def test_validate_handle_exception(self):
        record_set = create_test_recordset()
        rs_module = record_set.__class__.__bases__[0].__module__
        fn_name = f'{rs_module}.DesignateObject.obj_cls_from_name'

        with mock.patch(fn_name) as patched:
            patched.side_effect = KeyError
            self.assertRaisesRegex(
                exceptions.InvalidObject,
                'Provided object does not match schema',
                record_set.validate
            )

    def test_parse_rrset_object_preserves_changes(self):
        old_ip = '1.1.1.1'
        new_ip = '8.8.8.8'
        original_records = objects.RecordList(
            objects=[
                objects.Record(data=old_ip),
            ]
        )

        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=original_records
        )

        body = {
            'records': [
                new_ip
            ]
        }

        record_set = DesignateAdapter.parse('API_v2', body, record_set)
        self.assertIn('records', record_set.obj_what_changed())

        def get_data(record_list):
            return {r.data for r in record_list}

        self.assertEqual(
            {old_ip},
            get_data(record_set.obj_get_original_value('records'))
        )

        self.assertEqual(
            {new_ip},
            get_data(record_set.obj_get_changes()['records'])
        )

    def test_parse_rrset_object_preserves_changes_multiple_rrs(self):
        old_ips = ['1.1.1.1', '2.2.2.2']
        new_ips = ['2.2.2.2', '8.8.8.8']
        original_records = objects.RecordList(
            objects=[
                objects.Record(data=ip) for ip in old_ips
            ]
        )

        record_set = objects.RecordSet(
            name='www.example.org.', type='A',
            records=original_records
        )

        body = {
            'records': new_ips
        }

        record_set = DesignateAdapter.parse('API_v2', body, record_set)
        self.assertIn('records', record_set.obj_what_changed())

        def get_data(record_list):
            return {r.data for r in record_list}

        self.assertEqual(
            set(old_ips),
            get_data(record_set.obj_get_original_value('records'))
        )

        self.assertEqual(
            set(new_ips),
            get_data(record_set.obj_get_changes()['records'])
        )
