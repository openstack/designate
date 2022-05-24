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
from designate.common import constants
from designate.objects import base
from designate.objects import fields


@base.DesignateRegistry.register
class Quota(base.DictObjectMixin, base.PersistentObjectMixin,
            base.DesignateObject):
    fields = {
        'tenant_id': fields.AnyField(nullable=True),
        'resource': fields.EnumField(nullable=True,
                                     valid_values=constants.VALID_QUOTAS),
        'hard_limit': fields.IntegerFields(nullable=True,
                                           minimum=constants.MIN_QUOTA,
                                           maximum=constants.MAX_QUOTA)
    }

    STRING_KEYS = [
        'resource', 'tenant_id', 'hard_limit'
    ]


@base.DesignateRegistry.register
class QuotaList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = Quota

    fields = {
        'objects': fields.ListOfObjectsField('Quota'),
    }

    @classmethod
    def from_dict(cls, _dict):
        instance = cls()
        for field, value in _dict.items():
            item = cls.LIST_ITEM_TYPE()
            item.resource = field
            item.hard_limit = value
            instance.append(item)

        return instance

    def to_dict(self):
        _dict = {}
        for quota in self.objects:
            _dict[quota.resource] = quota.hard_limit
        return _dict
