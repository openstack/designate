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


class ZonesView(base_view.BaseView):
    """ Model a Zone API response as a python dictionary """

    _resource_name = 'zone'
    _collection_name = 'zones'

    def detail(self, context, request, zone):
        """ Detailed view of a zone """
        # TODO(kiall): pool_id should not be hardcoded.. even temp :)
        return {
            "zone": {
                "id": zone['id'],
                "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
                "project_id": zone['tenant_id'],
                "name": zone['name'],
                "email": zone['email'],
                "description": zone['description'],
                "ttl": zone['ttl'],
                "serial": zone['serial'],
                "status": zone['status'],
                "version": zone['version'],
                "created_at": zone['created_at'],
                "updated_at": zone['updated_at'],
                "links": self._get_resource_links(request, zone)
            }
        }

    def load(self, context, request, body):
        """ Extract a "central" compatible dict from an API call """
        result = {}
        item = body[self._resource_name]

        # Copy keys which need no alterations
        for k in ('id', 'name', 'email', 'description', 'ttl'):
            if k in item:
                result[k] = item[k]

        return result
