# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
from designate import objects
from designate.objects.adapters.yaml import base


class PoolAttributeYAMLAdapter(base.YAMLAdapter):
    ADAPTER_OBJECT = objects.PoolAttribute
    MODIFICATIONS = {
        'fields': {
            'key': {
                'read_only': False
            },
            'value': {
                'read_only': False
            },
        }
    }

    @classmethod
    def render_object(cls, obj, *arg, **kwargs):
        return {
            str(obj.key): str(obj.value)
        }

    @classmethod
    def parse_object(cls, values, obj, *args, **kwargs):
        for key in values.keys():
            obj.key = key
            obj.value = values[key]

        return obj


class PoolAttributeListYAMLAdapter(base.YAMLAdapter):
    ADAPTER_OBJECT = objects.PoolAttributeList
    MODIFICATIONS = {}

    @classmethod
    def render_list(cls, list_objects, *args, **kwargs):
        r_list = {}
        for obj in list_objects:
            adapter = cls.get_object_adapter(obj)
            value = adapter.render(cls.ADAPTER_FORMAT, obj, *args, **kwargs)
            for key in value.keys():
                r_list[key] = value[key]
        return r_list

    @classmethod
    def parse_list(cls, values, output_object, *args, **kwargs):
        for key, value in values.items():
            # Add the object to the list
            output_object.append(
                # Get the right Adapter
                cls.get_object_adapter(
                    # This gets the internal type of the list, and parses it
                    # We need to do `get_object_adapter` as we need a new
                    # instance of the Adapter
                    output_object.LIST_ITEM_TYPE()).parse(
                        {key: value}, output_object.LIST_ITEM_TYPE()
                )
            )

        return output_object
