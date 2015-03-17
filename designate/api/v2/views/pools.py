# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
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

from designate import objects
from designate.api.v2.views import base as base_view


LOG = logging.getLogger(__name__)


class PoolsView(base_view.BaseView):
    """Model a Pool API response as a python dictionary"""

    _resource_name = 'pool'
    _collection_name = 'pools'

    def show_basic(self, context, request, pool):
        """Basic view of a pool"""
        return {
            "id": pool['id'],
            "name": pool['name'],
            "project_id": pool['tenant_id'],
            "attributes": dict((r.key, r.value) for r in pool['attributes']),
            "ns_records": [{'priority': n.priority, 'hostname': n.hostname}
                           for n in pool['ns_records']],
            "description": pool['description'],
            "created_at": pool['created_at'],
            "updated_at": pool['updated_at'],
            "links": self._get_resource_links(request, pool)
        }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('name', 'attributes', 'ns_records', 'description')
        result = self._load(context, request, body, valid_keys)

        if 'ns_records' in result:
            result['ns_records'] = objects.PoolNsRecordList(
                objects=[objects.PoolNsRecord(priority=r['priority'],
                                              hostname=r['hostname'])
                         for r in result['ns_records']])

        if 'attributes' in result:
            result['attributes'] = objects.PoolAttributeList(
                objects=[objects.PoolAttribute(
                    key=r, value=result['attributes'][r])
                    for r in result['attributes']])
        return result
