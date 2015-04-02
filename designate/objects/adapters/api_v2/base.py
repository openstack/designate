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
import urllib

from oslo_log import log as logging
from oslo.config import cfg

from designate.objects.adapters import base
from designate.objects import base as obj_base

LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('api_base_uri', 'designate.api', group='service:api')


class APIv2Adapter(base.DesignateAdapter):

    BASE_URI = cfg.CONF['service:api'].api_base_uri.rstrip('/')

    ADAPTER_FORMAT = 'API_v2'

    #####################
    # Rendering methods #
    #####################

    @classmethod
    def _render_list(cls, list_object, *args, **kwargs):

        r_list = super(APIv2Adapter, cls)._render_list(
            list_object, *args, **kwargs)

        if cls.MODIFICATIONS['options'].get('links', True)\
                and 'request' in kwargs:
            r_list['links'] = cls._get_collection_links(
                list_object, kwargs['request'])
        # Check if we should include metadata
        if isinstance(list_object, obj_base.PagedListObjectMixin):
            metadata = {}
            metadata['total_count'] = list_object.total_count
            r_list['metadata'] = metadata

        return r_list

    @classmethod
    def _render_object(cls, object, *args, **kwargs):
        obj = super(APIv2Adapter, cls)._render_object(object, *args, **kwargs)

        if cls.MODIFICATIONS['options'].get('links', True)\
                and 'request' in kwargs:
            obj['links'] = cls._get_resource_links(object, kwargs['request'])

        return obj

    #####################
    #  Parsing methods  #
    #####################

    @classmethod
    def parse(cls, values, output_object, *args, **kwargs):
        return super(APIv2Adapter, cls).parse(
            cls.ADAPTER_FORMAT, values, output_object, *args, **kwargs)

    #####################
    #    Link methods   #
    #####################

    @classmethod
    def _get_resource_links(cls, object, request):
        return {'self': '%s%s/%s' %
                (cls.BASE_URI, cls._get_path(request), object.id)}

    @classmethod
    def _get_path(cls, request):
        path = request.path.lstrip('/').split('/')
        item_path = ''
        for part in path:
            if part == cls.MODIFICATIONS['options']['collection_name']:
                item_path += '/' + part
                return item_path
            else:
                item_path += '/' + part

    @classmethod
    def _get_collection_links(cls, list, request):

        links = {
            'self': cls._get_collection_href(request)
        }
        params = request.GET

        limit = cfg.CONF['service:api'].default_limit_v2

        if 'limit' in params and params['limit'] == 'max':
            limit = cfg.CONF['service:api'].max_limit_v2

        elif 'limit' in params:
            limit = int(params['limit'])

        if limit is not None and limit == len(list):
            links['next'] = cls._get_next_href(request, list)

        return links

    @classmethod
    def _get_collection_href(cls, request, extra_params=None):
        params = request.GET

        if extra_params is not None:
            params.update(extra_params)

        href = "%s%s?%s" % (
            cls.BASE_URI,
            cls._get_path(request),
            urllib.urlencode(params))

        return href.rstrip('?')

    @classmethod
    def _get_next_href(cls, request, items):
        # Prepare the extra params
        extra_params = {
            'marker': items[-1]['id']
        }

        return cls._get_collection_href(request, extra_params)
