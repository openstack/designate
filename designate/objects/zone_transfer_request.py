# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hpe.com>
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
class ZoneTransferRequest(base.DictObjectMixin, base.PersistentObjectMixin,
                          base.DesignateObject, ):
    fields = {
        'key': fields.StringFields(nullable=True, maxLength=160),
        'zone_id': fields.UUIDFields(nullable=True),
        'description': fields.StringFields(nullable=True, maxLength=160),
        'tenant_id': fields.StringFields(nullable=True),
        'target_tenant_id': fields.StringFields(nullable=True),
        'status': fields.EnumField(nullable=True, valid_values=[
            'ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE'
        ]),
        'zone_name': fields.StringFields(nullable=True, maxLength=255),
    }

    STRING_KEYS = [
        'id', 'zone_id', 'zone_name', 'target_tenant_id'
    ]


@base.DesignateRegistry.register
class ZoneTransferRequestList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = ZoneTransferRequest
    fields = {
        'objects': fields.ListOfObjectsField('ZoneTransferRequest'),
    }
