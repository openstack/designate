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
class PoolNameserver(base.DictObjectMixin, base.PersistentObjectMixin,
                     base.DesignateObject):
    fields = {
        'pool_id': fields.UUIDFields(nullable=True),
        'host': fields.IPOrHost(),
        'port': fields.IntegerFields(minimum=1, maximum=65535),
    }

    STRING_KEYS = [
        'id', 'host', 'port', 'pool_id'
    ]


@base.DesignateRegistry.register
class PoolNameserverList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = PoolNameserver
    fields = {
        'objects': fields.ListOfObjectsField('PoolNameserver'),
    }
