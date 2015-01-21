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
from oslo_log import log as logging

from designate import schema
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.views.zones.tasks import transfer_requests as \
    zone_transfer_requests_view
from designate.objects import ZoneTransferRequest

LOG = logging.getLogger(__name__)


class TransferRequestsController(rest.RestController):
    _view = zone_transfer_requests_view.ZoneTransferRequestsView()
    _resource_schema = schema.Schema('v2', 'transfer_request')
    _collection_schema = schema.Schema('v2', 'transfer_requests')
    SORT_KEYS = ['created_at', 'id', 'updated_at']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('transfer_request_id')
    def get_one(self, transfer_request_id):
        """Get transfer_request"""

        request = pecan.request
        context = request.environ['context']

        transfer_request = \
            self.central_api.get_zone_transfer_request(
                context, transfer_request_id)

        return self._view.show(context, request, transfer_request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List ZoneTransferRequests"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params.
        criterion = self._apply_filter_params(params, ('status',), {})

        zone_transfer_requests = self.central_api.find_zone_transfer_requests(
            context, criterion, marker, limit, sort_key, sort_dir)

        return self._view.list(context, request, zone_transfer_requests)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Create ZoneTransferRequest"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        if body['transfer_request'] is not None:
            body['transfer_request']['zone_id'] = zone_id

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the zone_transfer_request
        zone_transfer_request = self.central_api.create_zone_transfer_request(
            context, ZoneTransferRequest(**values))
        response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(
            request,
            zone_transfer_request)
        # Prepare and return the response body
        return self._view.show(context, request, zone_transfer_request)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('zone_transfer_request_id')
    def patch_one(self, zone_transfer_request_id):
        """Update ZoneTransferRequest"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # Fetch the existing zone_transfer_request
        zt_request = self.central_api.get_zone_transfer_request(
            context, zone_transfer_request_id)

        # Convert to APIv2 Format
        zt_request_data = self._view.show(context,
                                          request, zt_request)

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')
        else:
            zt_request_data = utils.deep_dict_merge(
                zt_request_data, body)

            # Validate the request conforms to the schema
            self._resource_schema.validate(zt_request_data)

            zt_request.update(self._view.load(context, request, body))
            zt_request = self.central_api.update_zone_transfer_request(
                context, zt_request)

        response.status_int = 200

        return self._view.show(context, request, zt_request)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('zone_transfer_request_id')
    def delete_one(self, zone_transfer_request_id):
        """Delete ZoneTransferRequest"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.delete_zone_transfer_request(
            context, zone_transfer_request_id)

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
