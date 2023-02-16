# Copyright 2020 Cloudification GmbH. All rights reserved.
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
class SharedZone(base.DictObjectMixin, base.PersistentObjectMixin,
                 base.DesignateObject):
    fields = {
        'zone_id': fields.UUIDFields(nullable=False),
        'project_id': fields.StringFields(maxLength=36, nullable=False),
        'target_project_id': fields.StringFields(maxLength=36, nullable=False),
    }

    STRING_KEYS = [
        'id', 'zone_id', 'project_id', 'target_project_id'
    ]


@base.DesignateRegistry.register
class SharedZoneList(base.AttributeListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = SharedZone

    fields = {
        'objects': fields.ListOfObjectsField('SharedZone'),
    }
