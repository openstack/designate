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
class ZoneTransferAccept(base.DictObjectMixin, base.PersistentObjectMixin,
                         base.DesignateObject):
    fields = {
        'zone_transfer_request_id': fields.UUIDFields(nullable=True),
        'tenant_id': fields.StringFields(nullable=True),
        'status': fields.EnumField(nullable=True, valid_values=[
            'ACTIVE', 'PENDING', 'DELETED', 'ERROR', 'COMPLETE'
        ]),
        'key': fields.StringFields(maxLength=160),
        'zone_id': fields.UUIDFields(nullable=True),
    }

    STRING_KEYS = [
        'id', 'zone_id', 'tenant_id', 'zone_transfer_request_id'
    ]


@base.DesignateRegistry.register
class ZoneTransferAcceptList(base.ListObjectMixin, base.DesignateObject,
                             base.PagedListObjectMixin):
    LIST_ITEM_TYPE = ZoneTransferAccept

    fields = {
        'objects': fields.ListOfObjectsField('ZoneTransferAccept'),
    }
