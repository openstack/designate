# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hp.com>
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
from oslo_log import log as logging

from designate.api.v2.views import base as base_view
from designate import exceptions
from designate import policy


LOG = logging.getLogger(__name__)


class ZoneTransferRequestsView(base_view.BaseView):
    """Model a ZoneTransferRequest API response as a python dictionary"""

    _resource_name = 'transfer_request'
    _collection_name = 'transfer_requests'

    def _get_base_href(self, parents=None):
        href = "%s/v2/zones/tasks/%s" % (self.base_uri, self._collection_name)
        return href.rstrip('?')

    def show_basic(self, context, request, zt_request):
        """Basic view of a ZoneTransferRequest"""

        try:
            target = {
                'tenant_id': zt_request.tenant_id,
            }

            policy.check('get_zone_transfer_request_detailed', context, target)

        except exceptions.Forbidden:
            return {
                "id": zt_request.id,
                "description": zt_request.description,
                "zone_id": zt_request.domain_id,
                "zone_name": zt_request.domain_name,
                "status": zt_request.status,
                "links": self._get_resource_links(request, zt_request)
            }
        else:
            return {
                "id": zt_request.id,
                "description": zt_request.description,
                "zone_id": zt_request.domain_id,
                "zone_name": zt_request.domain_name,
                "target_project_id": zt_request.target_tenant_id,
                "project_id": zt_request.tenant_id,
                "created_at": zt_request.created_at,
                "updated_at": zt_request.updated_at,
                "status": zt_request.status,
                "key": zt_request.key,
                "links": self._get_resource_links(request, zt_request)
            }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('description', 'domain_id', 'target_tenant_id')

        zt_request = body["transfer_request"]
        old_keys = {
            'zone_id': 'domain_id',
            'project_id': 'tenant_id',
            'target_project_id': 'target_tenant_id',
        }
        for key in zt_request:
            if key in old_keys:
                zt_request[old_keys[key]] = ''
                zt_request[old_keys[key]] = zt_request.pop(key)

        return self._load(context, request, body, valid_keys)
