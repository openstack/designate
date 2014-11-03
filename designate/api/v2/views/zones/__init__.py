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
from oslo_log import log as logging

from designate.api.v2.views import base as base_view


LOG = logging.getLogger(__name__)


class ZonesView(base_view.BaseView):
    """Model a Zone API response as a python dictionary"""

    _resource_name = 'zone'
    _collection_name = 'zones'

    def show_basic(self, context, request, zone):
        """Basic view of a zone"""
        values = {
            "id": zone['id'],
            "pool_id": zone['pool_id'],
            "project_id": zone['tenant_id'],
            "name": zone['name'],
            "type": zone['type'],
            "email": zone['email'],
            "description": zone['description'],
            "ttl": zone['ttl'],
            "serial": zone['serial'],
            "status": zone['status'],
            "action": zone['action'],
            "version": zone['version'],
            "created_at": zone['created_at'],
            "updated_at": zone['updated_at'],
            "transferred_at": zone['transferred_at'],
            "masters": zone.masters,
            "links": self._get_resource_links(request, zone)
        }

        return values

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        zone_keys = ('name', 'description', 'type', 'email', 'masters', 'ttl')
        return self._load(context, request, body, zone_keys)
