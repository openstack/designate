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


LOG = logging.getLogger(__name__)


class ZoneTransferAcceptsView(base_view.BaseView):
    """Model a ZoneTransferRequest API response as a python dictionary"""

    _resource_name = 'transfer_accept'
    _collection_name = 'transfer_accepts'

    def _get_base_href(self, parents=None):
        href = "%s/v2/zones/tasks/%s" % (self.base_uri, self._collection_name)
        return href.rstrip('?')

    def _get_resource_links(self, request, item):
        return {
            "self": self._get_resource_href(request, item),
            "zone": "%s/v2/zones/%s" % (self.base_uri, item.domain_id)
        }

    def show_basic(self, context, request, zt_accept):
        """Basic view of a ZoneTransferRequest"""

        return {
            "id": zt_accept.id,
            "status": zt_accept.status,
            "links": self._get_resource_links(request, zt_accept)
        }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('zone_transfer_request_id', 'key')

        return self._load(context, request, body, valid_keys)
