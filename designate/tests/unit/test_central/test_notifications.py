# Copyright 2016 Rackspace
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
import unittest

import mock
from oslo_log import log as logging

from designate import objects
from designate import notifications

LOG = logging.getLogger(__name__)


class DefaultNotificationTest(unittest.TestCase):

    def setUp(self):
        self.driver = notifications.Default()

        self.context = mock.Mock()

    def test_default_notifications(self):
        result = 'result'
        event = 'dns.zone.create'
        args = ('foo', 'bar',)
        kwargs = {'wumbo': 'mumbo'}

        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, ['result'])


class AuditNotificationTest(unittest.TestCase):

    def setUp(self):
        self.driver = notifications.Audit()

        self.context = mock.Mock()
        self.maxDiff = None

    #
    # Zone changes
    #

    def test_audit_zone_name(self):
        zone = objects.Zone(
                name='example.com.',
                type='PRIMARY',
        )

        result = zone
        event = 'dns.zone.create'
        args = (zone,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': None,
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_zone_id(self):
        zone = objects.Zone(
                id='123',
                name='example.com.',
                type='PRIMARY',
        )

        result = zone
        event = 'dns.zone.create'
        args = (zone,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_zone_update(self):
        zone = objects.Zone(
                id='123',
                name='example.com.',
                type='PRIMARY',
                ttl=1
        )
        zone.ttl = 300

        result = zone
        event = 'dns.zone.update'
        args = (zone,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': 'ttl',
            'new_data': '300',
            'old_data': '1',
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_zone_delete(self):
        zone = objects.Zone(
                id='123',
                name='example.com.',
                type='PRIMARY',
                ttl=1
        )

        result = zone
        event = 'dns.zone.delete'
        args = ('123',)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    #
    # Recordset Changes
    #

    def test_audit_rrset_name(self):
        rrset = objects.RecordSet(
                name='foo.example.com.',
                type='PRIMARY',
                records=objects.RecordList.from_list([])
        )

        rrset.records = objects.RecordList.from_list(
            [{'data': '192.168.1.1'}])

        result = rrset
        event = 'dns.recordset.create'
        args = (rrset,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': 'records',
            'new_data': '192.168.1.1',
            'old_data': '',
            'recordset_name': 'foo.example.com.',
            'zone_id': None,
            'zone_name': None
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_rrset_create(self):
        rrset = objects.RecordSet(
                name='foo.example.com.',
                type='PRIMARY',
                records=[],
                zone_id='123',
                zone_name='example.com.'
        )

        rrset.records = objects.RecordList.from_list(
            [{'data': '192.168.1.1'}])

        result = rrset
        event = 'dns.recordset.create'
        args = (rrset,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': 'records',
            'new_data': '192.168.1.1',
            'old_data': '',
            'recordset_name': 'foo.example.com.',
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_rrset_update_records(self):
        rrset = objects.RecordSet(
                name='foo.example.com.',
                type='PRIMARY',
                records=objects.RecordList.from_list(
                    [{'data': '192.168.1.1'}]),
                zone_id='123',
                zone_name='example.com.'
        )

        rrset.records = objects.RecordList.from_list(
            [{'data': '192.168.1.2'}])

        result = rrset
        event = 'dns.recordset.update'
        args = (rrset,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': 'records',
            'new_data': '192.168.1.2',
            'old_data': '192.168.1.1',
            'recordset_name': 'foo.example.com.',
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_rrset_update_other(self):
        rrset = objects.RecordSet(
                name='foo.example.com.',
                type='PRIMARY',
                records=objects.RecordList.from_list(
                    [{'data': '192.168.1.1'}]),
                zone_id='123',
                zone_name='example.com.',
                ttl=300
        )

        rrset.ttl = 400

        result = rrset
        event = 'dns.recordset.update'
        args = (rrset,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': 'ttl',
            'new_data': '400',
            'old_data': '300',
            'recordset_name': 'foo.example.com.',
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_rrset_delete(self):
        rrset = objects.RecordSet(
                name='foo.example.com.',
                type='PRIMARY',
                records=objects.RecordList.from_list([]),
                zone_id='123',
                zone_name='example.com.',
                id='1',
        )

        result = rrset
        event = 'dns.recordset.delete'
        args = ('123', '1',)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': 'foo.example.com.',
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    #
    # Zone Imports
    #

    def test_audit_import_create(self):
        zimport = objects.ZoneImport(
                zone_id='123',
        )

        result = zimport
        event = 'dns.zone_import.create'
        args = (zimport,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': None
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_import_delete(self):
        zimport = objects.ZoneImport(
                zone_id='123',
        )

        result = zimport
        event = 'dns.zone_import.create'
        args = ('1')
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': None
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    #
    # Zone Exports
    #

    def test_audit_export_create(self):
        zexport = objects.ZoneExport(
                zone_id='123',
        )

        result = zexport
        event = 'dns.zone_export.create'
        args = (zexport,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': None
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_export_delete(self):
        zexport = objects.ZoneExport(
                zone_id='123',
        )

        result = zexport
        event = 'dns.zone_export.create'
        args = ('1')
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': None
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    #
    # Zone Transfer Requests
    #
    def test_audit_transfer_request_create(self):
        ztransfer_request = objects.ZoneTransferRequest(
                zone_id='123',
                zone_name='example.com.',
                target_tenant_id='tenant_a',
        )

        result = ztransfer_request
        event = 'dns.zone_transfer_request.create'
        args = (ztransfer_request,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_transfer_request_update(self):
        ztransfer_request = objects.ZoneTransferRequest(
                zone_id='123',
                zone_name='example.com.',
                target_tenant_id='tenant_a',
        )

        ztransfer_request.target_tenant_id = 'tenant_b'

        result = ztransfer_request
        event = 'dns.zone_transfer_request.update'
        args = (ztransfer_request,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': 'target_tenant_id',
            'new_data': 'tenant_b',
            'old_data': 'tenant_a',
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    def test_audit_transfer_request_delete(self):
        ztransfer_request = objects.ZoneTransferRequest(
                zone_id='123',
                zone_name='example.com.',
                target_tenant_id='tenant_a',
        )

        result = ztransfer_request
        event = 'dns.zone_transfer_request.create'
        args = ('1')
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': 'example.com.'
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)

    #
    # Zone Transfer Requests
    #
    def test_audit_transfer_accept_create(self):
        ztransfer_accept = objects.ZoneTransferAccept(
                zone_id='123',
        )

        result = ztransfer_accept
        event = 'dns.zone_transfer_accept.create'
        args = (ztransfer_accept,)
        kwargs = {'wumbo': 'mumbo'}

        expected = [{
            'changed_field': None,
            'new_data': None,
            'old_data': None,
            'recordset_name': None,
            'zone_id': '123',
            'zone_name': None
        }]
        driver_result = self.driver.emit(
            event, self.context, result, args, kwargs)
        self.assertEqual(driver_result, expected)
