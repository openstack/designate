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
from urllib import parse

import designate.conf
from designate import exceptions
from designate.objects.adapters import base
from designate.objects import base as ovoobj_base


CONF = designate.conf.CONF


class APIv2Adapter(base.DesignateAdapter):
    ADAPTER_FORMAT = 'API_v2'

    #####################
    # Rendering methods #
    #####################

    @classmethod
    def render_list(cls, list_objects, *args, **kwargs):
        r_list = super().render_list(
            list_objects, *args, **kwargs)

        if (cls.MODIFICATIONS['options'].get('links', True) and
                'request' in kwargs):
            r_list['links'] = cls._get_collection_links(
                list_objects, kwargs['request']
            )
        # Check if we should include metadata
        if isinstance(list_objects, ovoobj_base.PagedListObjectMixin):
            metadata = {}
            if list_objects.total_count is not None:
                metadata['total_count'] = list_objects.total_count
            r_list['metadata'] = metadata

        return r_list

    @classmethod
    def render_object(cls, obj, *args, **kwargs):
        new_obj = super().render_object(obj, *args, **kwargs)

        if (cls.MODIFICATIONS['options'].get('links', True) and
                'request' in kwargs):
            new_obj['links'] = cls._get_resource_links(obj, kwargs['request'])

        return new_obj

    #####################
    #  Parsing methods  #
    #####################

    @classmethod
    def parse(cls, values, output_object, *args, **kwargs):
        return super().parse(
            cls.ADAPTER_FORMAT, values, output_object, *args, **kwargs)

    #####################
    #    Link methods   #
    #####################

    @classmethod
    def _get_base_url(cls, request):
        if CONF['service:api'].enable_host_header:
            return request.host_url
        return CONF['service:api'].api_base_uri.rstrip('/')

    @classmethod
    def _get_resource_links(cls, obj, request):
        base_uri = cls._get_base_url(request)

        path = cls._get_path(request, obj)
        return {'self': f'{base_uri}{path}/{obj.id}'}

    @classmethod
    def _get_path(cls, request, *args):
        path = request.path.lstrip('/').split('/')
        item_path = ''
        for part in path:
            if part == cls.MODIFICATIONS['options']['collection_name']:
                item_path += '/' + part
                return item_path
            else:
                item_path += '/' + part

    @classmethod
    def _get_collection_links(cls, item_list, request):

        links = {
            'self': cls._get_collection_href(request)
        }
        params = request.GET

        # defined in etc/designate/designate.conf.sample
        limit = CONF['service:api'].default_limit_v2

        if 'limit' in params:
            limit = params['limit']
            if limit.lower() == 'max':
                limit = CONF['service:api'].max_limit_v2
            else:
                try:
                    limit = int(limit)
                except ValueError:
                    raise exceptions.ValueError(
                        "'limit' should be an integer or 'max'")

        # Bug: this creates a link to "next" even on the last page if
        # len(item_list) happens to be == limit
        if limit is not None and limit == len(item_list):
            links['next'] = cls._get_next_href(request, item_list)

        return links

    @classmethod
    def _get_collection_href(cls, request, extra_params=None):
        params = request.GET

        if extra_params is not None:
            params.update(extra_params)

        base_uri = cls._get_base_url(request)

        href = '{}{}?{}'.format(
            base_uri,
            cls._get_path(request),
            parse.urlencode(params))

        return href.rstrip('?')

    @classmethod
    def _get_next_href(cls, request, items):
        # Prepare the extra params
        extra_params = {
            'marker': items[-1]['id']
        }

        return cls._get_collection_href(request, extra_params)
