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
class PoolTarget(base.DictObjectMixin, base.PersistentObjectMixin,
                 base.DesignateObject):
    fields = {
        'pool_id': fields.UUIDFields(nullable=True),
        'type': fields.AnyField(nullable=True),
        'tsigkey_id': fields.UUIDFields(nullable=True),
        'description': fields.StringFields(maxLength=160, nullable=True),
        'masters': fields.ObjectFields('PoolTargetMasterList'),
        'options': fields.ObjectFields('PoolTargetOptionList'),
        'backend': fields.AnyField(nullable=True),
    }

    STRING_KEYS = [
        'id', 'type', 'pool_id'
    ]


@base.DesignateRegistry.register
class PoolTargetList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = PoolTarget
    fields = {
        'objects': fields.ListOfObjectsField('PoolTarget'),
    }
