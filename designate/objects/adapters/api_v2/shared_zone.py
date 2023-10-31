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
from urllib import parse

from designate import objects
from designate.objects.adapters.api_v2 import base


class SharedZoneAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.SharedZone

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "zone_id": {},
            "project_id": {},
            "target_project_id": {'immutable': True},
            "created_at": {},
            "updated_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'shared_zone',
            'collection_name': 'shared_zones',
        }
    }

    @classmethod
    def render_object(cls, object, *args, **kwargs):
        obj = super().render_object(
            object, *args, **kwargs)

        if obj['zone_id'] is not None:
            obj['links']['self'] = (
                '{}/v2/zones/{}/shares/{}'.format(
                    cls._get_base_url(kwargs['request']), obj['zone_id'],
                    obj['id']))
            obj['links']['zone'] = (
                '{}/v2/zones/{}'.format(cls._get_base_url(kwargs['request']),
                                        obj['zone_id']))
        return obj


class SharedZoneListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.SharedZoneList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'shared_zone',
            'collection_name': 'shared_zones',
        }
    }

    @classmethod
    def _get_collection_href(cls, request, extra_params=None):
        params = request.GET

        if extra_params is not None:
            params.update(extra_params)

        base_uri = cls._get_base_url(request)

        href = '{}{}?{}'.format(
            base_uri,
            request.path,
            parse.urlencode(params))

        return href.rstrip('?')
