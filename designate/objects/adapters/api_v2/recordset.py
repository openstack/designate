# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
from designate import exceptions
from designate import objects
from designate.objects.adapters.api_v2 import base


class RecordSetAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.RecordSet
    MODIFICATIONS = {
        'fields': {
            "id": {},
            "zone_id": {},
            "project_id": {
                'rename': 'tenant_id'
            },
            "name": {
                'immutable': True
            },
            "zone_name": {
                'read_only': True,
            },
            "type": {
                'rename': 'type',
                'immutable': True
            },
            "records": {
                'read_only': False
            },
            "description": {
                'read_only': False
            },
            "ttl": {
                'read_only': False
            },
            "status": {},
            "action": {},
            "version": {},
            "created_at": {},
            "updated_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'recordset',
            'collection_name': 'recordsets',
        }
    }

    @classmethod
    def parse_object(cls, new_recordset, recordset, *args, **kwargs):
        # TODO(Graham): Remove this when
        # https://bugs.launchpad.net/designate/+bug/1432842 is fixed
        try:
            recordset.records
        except exceptions.RelationNotLoaded:
            recordset.records = objects.RecordList()

        original_records = set()
        for record in recordset.records:
            original_records.add(record.data)
        # Get new list of Records
        new_records = set()
        if 'records' in new_recordset:
            if isinstance(new_recordset['records'], list):
                for record in new_recordset['records']:
                    new_records.add(record)
            else:
                errors = objects.ValidationErrorList()
                e = objects.ValidationError()
                e.path = ['records']
                e.validator = 'type'
                e.validator_value = ["list"]
                e.message = ("'%(data)s' is not a valid list of records"
                             % {'data': new_recordset['records']})
                # Add it to the list for later
                errors.append(e)
                raise exceptions.InvalidObject(
                    "Provided object does not match "
                    "schema", errors=errors, object=cls.ADAPTER_OBJECT())

        # Get differences of Records
        records_to_add = new_records.difference(original_records)
        records_to_rm = original_records.difference(new_records)

        # Update all items except records
        record_update = False
        if 'records' in new_recordset:
            record_update = True
            del new_recordset['records']

        if record_update:
            # Build a list of the "new" records
            new_recordset_records = objects.RecordList()

            # Remove deleted records if we have provided a records array
            for record in recordset.records:
                if record.data not in records_to_rm:
                    new_recordset_records.append(record)

            # Add new records
            for record in records_to_add:
                new_recordset_records.append(objects.Record(data=record))

            # Do a single assignment, preserves the object change fields
            recordset.records = new_recordset_records

        return super().parse_object(
            new_recordset, recordset, *args, **kwargs)

    @classmethod
    def _get_path(cls, request, obj):
        ori_path = request.path
        path = ori_path.lstrip('/').split('/')
        insert_zones = False
        to_insert = ''
        if 'zones' not in path and obj is not None:
            insert_zones = True
            to_insert = f'zones/{obj.zone_id}'

        item_path = ''
        for part in path:
            if part == cls.MODIFICATIONS['options']['collection_name']:
                item_path += '/' + part
                return item_path
            elif insert_zones and to_insert and part == 'v2':
                item_path += f'/v2/{to_insert}'
                insert_zones = False  # make sure only insert once if needed
            else:
                item_path += '/' + part


class RecordSetListAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.RecordSetList
    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'recordset',
            'collection_name': 'recordsets',
        }
    }
