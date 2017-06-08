# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
class PoolManagerStatus(base.DictObjectMixin, base.PersistentObjectMixin,
                        base.DesignateObject):
    fields = {
        'nameserver_id': fields.UUIDFields(),
        'zone_id': fields.UUIDFields(),
        'status': fields.EnumField(['ACTIVE', 'PENDING', 'ERROR',
                                    'SUCCESS', 'COMPLETE'], nullable=True),
        'serial_number': fields.IntegerFields(minimum=0, maximum=4294967295),
        'action': fields.EnumField(['CREATE', 'DELETE',
                                    'UPDATE', 'NONE'], nullable=True),
    }

    STRING_KEYS = [
        'id', 'action', 'status', 'server_id', 'zone_id'
    ]


@base.DesignateRegistry.register
class PoolManagerStatusList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = PoolManagerStatus
    fields = {
        'objects': fields.ListOfObjectsField('PoolManagerStatus'),
    }
