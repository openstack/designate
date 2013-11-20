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
from designate.api.v2.views import base as base_view
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class RecordsView(base_view.BaseView):
    """ Model a Record API response as a python dictionary """

    _resource_name = 'record'
    _collection_name = 'records'

    def detail(self, context, request, record):
        """ Detailed view of a record """
        return {
            "record": {
                "id": record['id'],
                "recordset_id": record['recordset_id'],
                "data": record['data'],
                "description": record['description'],
                "version": record['version'],
                "created_at": record['created_at'],
                "updated_at": record['updated_at'],
                "links": self._get_resource_links(request, record)
            }
        }

    def load(self, context, request, body):
        """ Extract a "central" compatible dict from an API call """
        result = {}
        item = body[self._resource_name]

        # Copy keys which need no alterations
        for k in ('id', 'data', 'description',):
            if k in item:
                result[k] = item[k]

        return result
