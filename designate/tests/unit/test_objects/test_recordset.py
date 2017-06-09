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
import unittest

from oslo_log import log as logging
import mock
import oslotest.base
import testtools

from designate import exceptions
from designate.objects.adapters import DesignateAdapter
from designate import objects

LOG = logging.getLogger(__name__)


def debug(*a, **kw):
    for v in a:
        LOG.debug(repr(v))

    for k in sorted(kw):
        LOG.debug("%s: %s", k, repr(kw[k]))


class TestRecordSet(objects.RecordSet):
    FIELDS = {
        'id': {},
        'name': {},
        'records': {
            'relation': True,
            'relation_cls': 'RecordList',
        },
    }


def create_test_recordset():
    rs = objects.RecordSet(
        name='www.example.org.',
        type='A',
        records=objects.RecordList(objects=[
            objects.Record(data='192.0.2.1'),
            objects.Record(data='192.0.2.2'),
        ])
    )
    return rs


class RecordSetTest(oslotest.base.BaseTestCase):

    def test_init(self):
        rs = create_test_recordset()
        self.assertEqual('www.example.org.', rs.name)
        self.assertEqual('A', rs.type)

    def test_not_managed(self):
        rs = create_test_recordset()
        self.assertFalse(rs.managed)

    def test_managed(self):
        rs = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', managed=True),
                objects.Record(data='192.0.2.2'),
            ])
        )
        self.assertTrue(rs.managed)

    def test_action(self):
        action = 'CREATE'
        rs = objects.RecordSet(
            name='www.example.org.',
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action=action),
            ])
        )
        self.assertEqual(action, rs.action)

    def test_action_create(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='CREATE'),
            ])
        )
        self.assertEqual('CREATE', rs.action)

    def test_action_create_plus_update(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='CREATE'),
                objects.Record(data='192.0.2.2', action='UPDATE'),
            ])
        )
        self.assertEqual('UPDATE', rs.action)

    def test_action_delete_plus_update(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='DELETE'),
                objects.Record(data='192.0.2.2', action='UPDATE'),
            ])
        )
        self.assertEqual('UPDATE', rs.action)

    def test_action_delete_only(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1', action='DELETE'),
                objects.Record(data='192.0.2.2', action='DELETE'),
            ])
        )
        self.assertEqual('DELETE', rs.action)

    @unittest.expectedFailure  # bug
    def test_status_error(self):
        statuses = ('ERROR', 'PENDING', 'ACTIVE')
        failed = False
        for s1, s2, s3 in itertools.permutations(statuses):
            rs = objects.RecordSet(
                name='www.example.org.', type='A',
                records=objects.RecordList(objects=[
                    objects.Record(data='192.0.2.1', status=s1),
                    objects.Record(data='192.0.2.2', status=s2),
                    objects.Record(data='192.0.2.3', status=s3),
                ])
            )
            if rs.status != 'ERROR':
                failed = True
                print("test_status_error failed for %s %s %s: %s" % (
                    s1, s2, s3, rs.status))

        self.assertFalse(failed)

    def test_status_pending(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2', status='PENDING'),
                objects.Record(data='192.0.2.3', status='ACTIVE'),
            ])
        )
        self.assertEqual('PENDING', rs.status)

    def test_status_pending2(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.3', status='ACTIVE'),
                objects.Record(data='192.0.2.2', status='PENDING'),
            ])
        )
        self.assertEqual('PENDING', rs.status)

    def test_status_active(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.3', status='ACTIVE'),
            ])
        )
        self.assertEqual('ACTIVE', rs.status)

    def test_status_deleted(self):
        rs = objects.RecordSet(
            name='www.example.org.', type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.2', status='DELETED'),
            ])
        )
        self.assertEqual('DELETED', rs.status)

    def test_validate(self):
        rs = create_test_recordset()
        rs.validate()

    def test_validate_handle_exception(self):
        rs = create_test_recordset()
        fn_name = 'designate.objects.DesignateObject.obj_cls_from_name'
        with mock.patch(fn_name) as patched:
            patched.side_effect = KeyError
            with testtools.ExpectedException(exceptions.InvalidObject):
                # TODO(Federico): check the attributes of the exception
                rs.validate()

    def test_parse_rrset_object_preserves_changes(self):
        old_ip = '1.1.1.1'
        new_ip = '8.8.8.8'
        original_records = objects.RecordList(
            objects=[
                objects.Record(data=old_ip),
            ]
        )

        rs = objects.RecordSet(
                name='www.example.org.', type='A',
                records=original_records
        )

        body = {
            'records': [
                new_ip
            ]
        }

        rs = DesignateAdapter.parse('API_v2', body, rs)
        self.assertIn('records', rs.obj_what_changed())

        def get_data(record_list):
            return set([r.data for r in record_list])

        self.assertEqual(set([old_ip]),
            get_data(rs.obj_get_original_value('records')))

        self.assertEqual(set([new_ip]),
            get_data(rs.obj_get_changes()['records']))

    def test_parse_rrset_object_preserves_changes_multiple_rrs(self):
        old_ips = ['1.1.1.1', '2.2.2.2']
        new_ips = ['2.2.2.2', '8.8.8.8']
        original_records = objects.RecordList(
            objects=[
                objects.Record(data=ip) for ip in old_ips
            ]
        )

        rs = objects.RecordSet(
                name='www.example.org.', type='A',
                records=original_records
        )

        body = {
            'records': new_ips
        }

        rs = DesignateAdapter.parse('API_v2', body, rs)
        self.assertIn('records', rs.obj_what_changed())

        def get_data(record_list):
            return set([r.data for r in record_list])

        self.assertEqual(set(old_ips),
            get_data(rs.obj_get_original_value('records')))

        self.assertEqual(set(new_ips),
            get_data(rs.obj_get_changes()['records']))
