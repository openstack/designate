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
class Tenant(base.DesignateObject, base.DictObjectMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    fields = {
        'id': fields.AnyField(nullable=True),
        'zone_count': fields.AnyField(nullable=True),
        'zones': fields.AnyField(nullable=True)
    }

    STRING_KEYS = [
        'id'
    ]


@base.DesignateRegistry.register
class TenantList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Tenant

    fields = {
        'objects': fields.ListOfObjectsField('Tenant'),
    }
