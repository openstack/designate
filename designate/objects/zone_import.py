# Copyright 2015 Rackspace Inc.
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
from designate.objects import base
from designate.objects import fields


@base.DesignateRegistry.register
class ZoneImport(base.DictObjectMixin, base.PersistentObjectMixin,
                 base.DesignateObject):
    fields = {
        'status': fields.EnumField(
            nullable=True, valid_values=[
                'ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE'
            ]
        ),
        'task_type': fields.EnumField(
            nullable=True, valid_values=['IMPORT']
        ),
        'tenant_id': fields.StringFields(nullable=True),
        'message': fields.StringFields(nullable=True, maxLength=160),
        'zone_id': fields.UUIDFields(nullable=True)
    }


@base.DesignateRegistry.register
class ZoneImportList(base.ListObjectMixin, base.DesignateObject,
                     base.PagedListObjectMixin):
    LIST_ITEM_TYPE = ZoneImport

    fields = {
        'objects': fields.ListOfObjectsField('ZoneImport'),
    }
