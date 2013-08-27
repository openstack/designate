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
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class BaseView(object):
    """
    The Views are responsible for coverting to/from the "intenal" and
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

    def list(self, context, request, items):
        """ View of a list of items """
        result = {
            "links": self._get_collection_links(request, items)
        }

        if 'detail' in request.GET and request.GET['detail'] == 'yes':
            result[self._collection_name] = [self.detail(context, request, i)
                                             for i in items]
        else:
            result[self._collection_name] = [self.basic(context, request, i)
                                             for i in items]

        return result

    def basic(self, context, request, item):
        """ Non-detailed view of a item """
        return self.detail(context, request, item)

    def _get_resource_links(self, request, item):
        return {
            "self": self._get_resource_href(request, item)
        }

    def _get_collection_links(self, request, items):
        # TODO(kiall): Next and previous links should only be included
        #              when there are more/previous items.. This is what nova
        #              does.. But I think we can do better.

        params = request.GET

        result = {
            "self": self._get_collection_href(request),
        }

        if 'marker' in params:
            result['previous'] = self._get_previous_href(request, items)

        if 'limit' in params and int(params['limit']) == len(items):
            result['next'] = self._get_next_href(request, items)

        return result

    def _get_resource_href(self, request, item):
        href = "%s/v2/%s/%s" % (self.base_uri, self._collection_name,
                                item['id'])

        return href.rstrip('?')

    def _get_collection_href(self, request):
        params = request.GET

        href = "%s/v2/%s?%s" % (self.base_uri, self._collection_name,
                                urllib.urlencode(params))

        return href.rstrip('?')

    def _get_next_href(self, request, items):
        params = request.GET

        # Add/Update the marker and sort_dir params
        params['marker'] = items[-1]['id']
        params.pop('sort_dir', None)

        return "%s/v2/%s?%s" % (self.base_uri, self._collection_name,
                                urllib.urlencode(params))

    def _get_previous_href(self, request, items):
        params = request.GET

        # Add/Update the marker and sort_dir params
        params['marker'] = items[0]['id']
        params['sort_dir'] = 'DESC'

        return "%s/v2/%s?%s" % (self.base_uri, self._collection_name,
                                urllib.urlencode(params))
