# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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
from oslo_log import log as logging

from designate.objects.adapters import base

LOG = logging.getLogger(__name__)


class YAMLAdapter(base.DesignateAdapter):

    ADAPTER_FORMAT = 'YAML'

    #####################
    #  Parsing methods  #
    #####################

    @classmethod
    def parse(cls, values, output_object, *args, **kwargs):
        obj = super().parse(
            cls.ADAPTER_FORMAT, values, output_object, *args, **kwargs)
        return obj

    @classmethod
    def render_object(cls, obj, *args, **kwargs):
        # The dict we will return to be rendered to JSON / output format
        r_obj = {}
        # Loop over all fields that are supposed to be output
        for key, value in cls.MODIFICATIONS['fields'].items():
            # Get properties for this field
            field_props = cls.MODIFICATIONS['fields'][key]
            # Check if it has to be renamed
            if field_props.get('rename', False):
                new_obj = getattr(obj, field_props.get('rename'))
                # if rename is specified we need to change the key
                obj_key = field_props.get('rename')
            else:
                # if not, move on
                new_obj = getattr(obj, key, None)
                obj_key = key

            if new_obj is None:
                continue

            # Check if this item is a relation (another DesignateObject that
            # will need to be converted itself
            if hasattr(obj.FIELDS.get(obj_key, {}), 'objname'):
                # Get a adapter for the nested object
                # Get the class the object is and get its adapter, then set
                # the item in the dict to the output
                adapter = cls.get_object_adapter(obj.FIELDS[obj_key].objname)
                r_obj[key] = adapter.render(cls.ADAPTER_FORMAT, new_obj, *args,
                                            **kwargs)
            elif all(hasattr(obj.FIELDS.get(obj_key, {}), attr)
                     for attr in ['min', 'max']):
                r_obj[key] = int(new_obj)
            elif new_obj is not None:
                # Just attach the damn item if there is no weird edge cases
                r_obj[key] = str(new_obj)
        # Send it back
        return r_obj

    @classmethod
    def render_list(cls, list_objects, *args, **kwargs):
        r_list = []
        for obj in list_objects:
            adapter = cls.get_object_adapter(obj)
            r_list.append(
                adapter.render(cls.ADAPTER_FORMAT, obj, *args, **kwargs)
            )
        return r_list
