# Copyright (c) 2014 Rackspace Hosting
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
from designate.objects import base
from designate.objects import fields


@base.DesignateRegistry.register
class Record(base.DesignateObject, base.PersistentObjectMixin,
             base.DictObjectMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    fields = {
        'shard': fields.IntegerFields(nullable=True, minimum=0, maximum=4095),
        'data': fields.AnyField(nullable=True),
        'zone_id': fields.UUIDFields(nullable=True),
        'managed': fields.BooleanField(nullable=True),
        'managed_resource_type': fields.StringFields(nullable=True,
                                                     maxLength=160),
        'managed_resource_id': fields.UUIDFields(nullable=True),
        'managed_plugin_name': fields.StringFields(nullable=True,
                                                   maxLength=160),
        'managed_plugin_type': fields.StringFields(nullable=True,
                                                   maxLength=160),
        'hash': fields.StringFields(nullable=True, maxLength=32),
        'description': fields.StringFields(nullable=True,
                                           maxLength=160),
        'status': fields.EnumField(
            valid_values=['ACTIVE', 'PENDING', 'ERROR', 'DELETED'],
            nullable=True
        ),
        'tenant_id': fields.StringFields(nullable=True),
        'recordset_id': fields.UUIDFields(nullable=True),
        'managed_tenant_id': fields.StringFields(nullable=True),
        'managed_resource_region': fields.StringFields(nullable=True,
                                                       maxLength=160),
        'managed_extra': fields.StringFields(nullable=True,
                                             maxLength=160),
        'action': fields.EnumField(
            valid_values=['CREATE', 'DELETE', 'UPDATE', 'NONE'],
            nullable=True
        ),
        'serial': fields.IntegerFields(nullable=True,
                                       minimum=1, maximum=4294967295),
    }

    @classmethod
    def get_recordset_schema_changes(cls):
        # This is to allow record types to override the validation on a
        # recordset
        return {}

    STRING_KEYS = [
        'id', 'recordset_id', 'data'
    ]

    def __repr__(self):
        record = self.to_dict()
        if record.get('data') is not None:
            record['data'] = record['data'][:35]
        return self._make_obj_str(record)


@base.DesignateRegistry.register
class RecordList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Record

    fields = {
        'objects': fields.ListOfObjectsField('Record'),
    }
