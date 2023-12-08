# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
from designate.common import constants
from designate.objects import base
from designate.objects import fields


@base.DesignateRegistry.register
class FloatingIP(base.DictObjectMixin, base.PersistentObjectMixin,
                 base.DesignateObject):
    fields = {
        "address": fields.IPV4AddressField(nullable=True),
        "description": fields.StringFields(nullable=True, maxLength=160),
        "ptrdname": fields.DomainField(nullable=True),
        "ttl": fields.IntegerFields(nullable=True,
                                    minimum=0, maximum=2147483647),
        "region": fields.StringFields(nullable=True),
        "action": fields.EnumField(constants.FLOATING_IP_ACTIONS,
                                   nullable=True),
        "status": fields.EnumField(constants.FLOATING_IP_STATUSES,
                                   nullable=True)
    }

    STRING_KEYS = [
        'key', 'address', 'ptrdname'
    ]

    @property
    def key(self):
        return f'{self.region}:{self.id}'


@base.DesignateRegistry.register
class FloatingIPList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = FloatingIP

    fields = {
        'objects': fields.ListOfObjectsField('FloatingIP'),
    }
