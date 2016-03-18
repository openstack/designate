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
        obj = super(YAMLAdapter, cls).parse(
            cls.ADAPTER_FORMAT, values, output_object, *args, **kwargs)
        return obj

    @classmethod
    def _render_object(cls, object, *args, **kwargs):
        # The dict we will return to be rendered to JSON / output format
        r_obj = {}
        # Loop over all fields that are supposed to be output
        for key, value in cls.MODIFICATIONS['fields'].items():
            # Get properties for this field
            field_props = cls.MODIFICATIONS['fields'][key]
            # Check if it has to be renamed
            if field_props.get('rename', False):
                obj = getattr(object, field_props.get('rename'))
                # if rename is specified we need to change the key
                obj_key = field_props.get('rename')
            else:
                # if not, move on
                obj = getattr(object, key, None)
                obj_key = key
            # Check if this item is a relation (another DesignateObject that
            # will need to be converted itself
            if object.FIELDS.get(obj_key, {}).get('relation'):
                # Get a adapter for the nested object
                # Get the class the object is and get its adapter, then set
                # the item in the dict to the output
                r_obj[key] = cls.get_object_adapter(
                    cls.ADAPTER_FORMAT,
                    object.FIELDS[obj_key].get('relation_cls')).render(
                        cls.ADAPTER_FORMAT, obj, *args, **kwargs)
            elif object.FIELDS.get(
                    obj_key, {}).get('schema', {}).get('type') == 'integer':
                r_obj[key] = int(obj)
            elif obj is not None:
                # Just attach the damn item if there is no weird edge cases
                r_obj[key] = str(obj)
        # Send it back
        return r_obj

    @classmethod
    def _render_list(cls, list_object, *args, **kwargs):
        # The list we will return to be rendered to JSON / output format
        r_list = []
        # iterate and convert each DesignateObject in the list, and append to
        # the object we are returning
        for object in list_object:
            r_list.append(cls.get_object_adapter(
                cls.ADAPTER_FORMAT,
                object).render(cls.ADAPTER_FORMAT, object, *args, **kwargs))
        return r_list
