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
import pecan

from designate.openstack.common import log as logging
from designate import schema
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.views.zones.tasks import transfer_accepts as \
    zone_transfer_accepts_view
from designate.objects import ZoneTransferAccept


LOG = logging.getLogger(__name__)


class TransferAcceptsController(rest.RestController):
    _view = zone_transfer_accepts_view.ZoneTransferAcceptsView()
    _resource_schema = schema.Schema('v2', 'transfer_accept')
    _collection_schema = schema.Schema('v2', 'transfer_accepts')
    SORT_KEYS = ['created_at', 'id', 'updated_at']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('transfer_accept_id')
    def get_one(self, transfer_accept_id):
        """Get transfer_accepts"""

        request = pecan.request
        context = request.environ['context']

        transfer_accepts = \
            self.central_api.get_zone_transfer_accept(
                context, transfer_accept_id)

        return self._view.show(context, request, transfer_accepts)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create ZoneTransferAccept"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)
        # Create the zone_transfer_request
        zone_transfer_accept = self.central_api.create_zone_transfer_accept(
            context, ZoneTransferAccept(**values))
        response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(
            request,
            zone_transfer_accept)
        # Prepare and return the response body
        return self._view.show(context, request, zone_transfer_accept)
