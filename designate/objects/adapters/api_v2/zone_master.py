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
from designate.objects.adapters.api_v2 import base
from designate import utils


class ZoneMasterAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.ZoneMaster
    MODIFICATIONS = {
        'fields': {
            'value': {
                'read_only': False
            }
        },
        'options': {
            'links': False,
            'resource_name': 'domain_master',
            'collection_name': 'domain_masters',
        }
    }

    @classmethod
    def render_object(cls, obj, *arg, **kwargs):
        if obj.port == 53:
            return obj.host
        else:
            return "%(host)s:%(port)d" % obj.to_dict()

    @classmethod
    def parse_object(cls, value, obj, *args, **kwargs):
        obj.host, obj.port = utils.split_host_port(value)
        return obj


class ZoneMasterListAPIv2Adapter(base.APIv2Adapter):
    ADAPTER_OBJECT = objects.ZoneMasterList
    MODIFICATIONS = {
        'options': {
            'links': False,
            'resource_name': 'domain_master',
            'collection_name': 'domain_masters',
        }
    }

    @classmethod
    def render_list(cls, list_objects, *args, **kwargs):
        r_list = []
        for obj in list_objects:
            adapter = cls.get_object_adapter(obj)
            r_list.append(
                adapter.render(cls.ADAPTER_FORMAT, obj, *args, **kwargs)
            )
        return r_list

    @classmethod
    def parse_list(cls, values, output_object, *args, **kwargs):
        for value in values:
            # Add the object to the list
            output_object.append(
                # Get the right Adapter
                cls.get_object_adapter(
                    # This gets the internal type of the list, and parses it
                    # We need to do `get_object_adapter` as we need a new
                    # instance of the Adapter
                    output_object.LIST_ITEM_TYPE()).parse(
                        value, output_object.LIST_ITEM_TYPE()
                )
            )

        return output_object
