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


class RecordSetsView(base_view.BaseView):
    """ Model a Zone API response as a python dictionary """

    _resource_name = 'recordset'
    _collection_name = 'recordsets'

    def detail(self, context, request, recordset):
        """ Detailed view of a recordset """
        return {
            "recordset": {
                "id": recordset['id'],
                "zone_id": recordset['domain_id'],
                "name": recordset['name'],
                "type": recordset['type'],
                "ttl": recordset['ttl'],
                "description": recordset['description'],
                "version": recordset['version'],
                "created_at": recordset['created_at'],
                "updated_at": recordset['updated_at'],
                "links": self._get_resource_links(request, recordset)
            }
        }

    def load(self, context, request, body):
        """ Extract a "central" compatible dict from an API call """
        result = {}
        item = body[self._resource_name]

        # Copy keys which need no alterations
        for k in ('id', 'name', 'type', 'ttl', 'description',):
            if k in item:
                result[k] = item[k]

        return result
