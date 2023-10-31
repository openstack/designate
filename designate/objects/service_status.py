# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
class ServiceStatus(base.DesignateObject, base.DictObjectMixin,
                    base.PersistentObjectMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    fields = {
        "service_name": fields.StringFields(),
        "hostname": fields.StringFields(nullable=True),
        "heartbeated_at": fields.DateTimeField(nullable=True),
        "status": fields.EnumField(nullable=True, valid_values=[
            "UP", "DOWN", "WARNING"
        ]),
        "stats": fields.BaseObjectField(nullable=True),
        "capabilities": fields.BaseObjectField(nullable=True),
    }

    STRING_KEYS = [
        'service_name', 'hostname', 'status'
    ]


@base.DesignateRegistry.register
class ServiceStatusList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = ServiceStatus

    fields = {
        'objects': fields.ListOfObjectsField('ServiceStatus'),
    }
