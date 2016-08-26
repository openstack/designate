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
import six

from designate.objects.adapters.yaml import base
from designate import objects


class PoolTargetOptionYAMLAdapter(base.YAMLAdapter):

    ADAPTER_OBJECT = objects.PoolTargetOption

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
    def _render_object(cls, object, *arg, **kwargs):
        return {str(object.key): str(object.value)}

    @classmethod
    def _parse_object(cls, values, object, *args, **kwargs):
        for key in six.iterkeys(values):
            object.key = key
            object.value = values[key]

        return object


class PoolTargetOptionListYAMLAdapter(base.YAMLAdapter):

    ADAPTER_OBJECT = objects.PoolTargetOptionList

    MODIFICATIONS = {}

    @classmethod
    def _render_list(cls, list_object, *args, **kwargs):

        r_list = {}

        for object in list_object:
            value = cls.get_object_adapter(
                cls.ADAPTER_FORMAT,
                object).render(cls.ADAPTER_FORMAT, object, *args, **kwargs)
            for key in six.iterkeys(value):
                r_list[key] = value[key]

        return r_list

    @classmethod
    def _parse_list(cls, values, output_object, *args, **kwargs):

        for key, value in values.items():
            # Add the object to the list
            output_object.append(
                # Get the right Adapter
                cls.get_object_adapter(
                    cls.ADAPTER_FORMAT,
                    # This gets the internal type of the list, and parses it
                    # We need to do `get_object_adapter` as we need a new
                    # instance of the Adapter
                    output_object.LIST_ITEM_TYPE()).parse(
                        {key: value}, output_object.LIST_ITEM_TYPE()))

        # Return the filled list
        return output_object
