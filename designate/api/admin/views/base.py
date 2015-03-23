# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import urllib

from oslo.config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import objects


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class BaseView(object):
    """
    The Views are responsible for coverting to/from the "internal" and
    "external" representations of collections and resources. This includes
    adding "links" and adding/removing any other wrappers returned/received
    as part of the API call.

    For example, in the V2 API, we did s/domain/zone/. Adapting a record
    resources "domain_id" <-> "zone_id" is the responsibility of a View.
    """
    _resource_name = None
    _collection_name = None

    def __init__(self):
        super(BaseView, self).__init__()

        self.base_uri = CONF['service:api']['api_base_uri'].rstrip('/')

    def list(self, context, request, items, parents=None, metadata=None):
        """View of a list of items"""
        result = {
            "links": self._get_collection_links(request, items, parents)
        }

        metadata = metadata or {}

        if isinstance(items, objects.base.PagedListObjectMixin):
            metadata['total_count'] = items.total_count

        result['metadata'] = metadata

        if 'detail' in request.GET and request.GET['detail'] == 'yes':
            result[self._collection_name] = self.list_detail(context, request,
                                                             items)
        else:
            result[self._collection_name] = self.list_basic(context, request,
                                                            items)

        return result

    def list_basic(self, context, request, items):
        """Non-detailed list of items"""
        return [self.show_basic(context, request, i) for i in items]

    def list_detail(self, context, request, items):
        """Detailed list of items"""
        return [self.show_detail(context, request, i) for i in items]

    def show(self, context, request, item):
        """Show a single item"""
        result = {}

        if 'detail' in request.GET and request.GET['detail'] == 'yes':
            result[self._resource_name] = self.show_detail(context, request,
                                                           item)
        else:
            result[self._resource_name] = self.show_basic(context, request,
                                                          item)

        return result

    def show_basic(self, context, request, item):
        """Non-detailed view of a item"""
        raise NotImplementedError()

    def show_detail(self, context, request, item):
        """Detailed view of a item"""
        return self.show_basic(context, request, item)

    def _load(self, context, request, body, valid_keys):
        """Extract a "central" compatible dict from an API call"""
        result = {}
        item = body[self._resource_name]
        error_keys = []

        # Copy keys which need no alterations
        for k in item:
            if k in valid_keys:
                result[k] = item[k]
            else:
                error_keys.append(k)

        if error_keys:
            error_message = str.format(
                'Provided object does not match schema.  Keys {0} are not '
                'valid in the request body',
                error_keys)

            raise exceptions.InvalidObject(error_message)

        return result

    def _get_resource_links(self, request, item, parents=None):
        return {
            "self": self._get_resource_href(request, item, parents),
        }

    def _get_collection_links(self, request, items, parents=None):
        # TODO(kiall): Next and previous links should only be included
        #              when there are more/previous items.. This is what nova
        #              does.. But I think we can do better.

        params = request.GET

        result = {
            "self": self._get_collection_href(request, parents),
        }

        # See above
        # if 'marker' in params:
        #    result['previous'] = self._get_previous_href(request, items,
        #                                                 parents)

        if 'limit' in params and int(params['limit']) == len(items):
            result['next'] = self._get_next_href(request, items, parents)

        return result

    def _get_base_href(self, parents=None):
        href = "%s/v2/%s" % (self.base_uri, self._collection_name)

        return href.rstrip('?')

    def _get_resource_href(self, request, item, parents=None):
        base_href = self._get_base_href(parents)
        href = "%s/%s" % (base_href, item['id'])

        return href.rstrip('?')

    def _get_collection_href(self, request, parents=None, extra_params=None):
        params = request.GET

        if extra_params is not None:
            params.update(extra_params)

        base_href = self._get_base_href(parents)

        href = "%s?%s" % (base_href, urllib.urlencode(params))

        return href.rstrip('?')

    def _get_next_href(self, request, items, parents=None):
        # Prepare the extra params
        extra_params = {
            'marker': items[-1]['id']
        }

        return self._get_collection_href(request, parents, extra_params)

    def _get_previous_href(self, request, items, parents=None):
        # Prepare the extra params
        extra_params = {
            'marker': items[0]['id']
        }

        return self._get_collection_href(request, parents, extra_params)
