# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hpe.com>
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

from designate import utils
from designate import exceptions
from designate.api.v2.controllers import rest
from designate.objects import ZoneTransferRequest
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI


LOG = logging.getLogger(__name__)


class TransferRequestsController(rest.RestController):

    SORT_KEYS = ['created_at', 'id', 'updated_at']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_transfer_request_id')
    def get_one(self, zone_transfer_request_id):
        """Get transfer_request"""

        request = pecan.request
        context = request.environ['context']

        transfer_request = self.central_api.get_zone_transfer_request(
            context, zone_transfer_request_id)

        LOG.info(_LI("Retrieved %(transfer_request)s"),
                 {'transfer_request': transfer_request})

        return DesignateAdapter.render(
            'API_v2',
            transfer_request,
            request=request,
            context=context)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List ZoneTransferRequests"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
                context, params, self.SORT_KEYS)

        # Extract any filter params.
        criterion = self._apply_filter_params(params, ('status',), {})

        zone_transfer_requests = self.central_api.find_zone_transfer_requests(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info(_LI("Retrieved %(zone_transfer_requests)s"),
                 {'zone_transfer_requests': zone_transfer_requests})

        return DesignateAdapter.render(
            'API_v2',
            zone_transfer_requests,
            request=request,
            context=context)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Create ZoneTransferRequest"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        try:
            body = request.body_dict
        except exceptions.EmptyRequestBody:
            body = dict()

        zone = self.central_api.get_zone(context, zone_id)
        body['zone_name'] = zone.name
        body['zone_id'] = zone_id

        zone_transfer_request = DesignateAdapter.parse(
            'API_v2', body, ZoneTransferRequest())

        zone_transfer_request.validate()

        # Create the zone_transfer_request
        zone_transfer_request = self.central_api.create_zone_transfer_request(
            context, zone_transfer_request)
        response.status_int = 201

        LOG.info(_LI("Created %(zone_transfer_request)s"),
                 {'zone_transfer_request': zone_transfer_request})

        zone_transfer_request = DesignateAdapter.render(
            'API_v2', zone_transfer_request, request=request, context=context)

        response.headers['Location'] = zone_transfer_request['links']['self']
        # Prepare and return the response body
        return zone_transfer_request

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('zone_transfer_request_id')
    def patch_one(self, zone_transfer_request_id):
        """Update ZoneTransferRequest"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')

        # Fetch the existing zone_transfer_request
        zone_transfer_request = self.central_api.get_zone_transfer_request(
            context, zone_transfer_request_id)

        zone_transfer_request = DesignateAdapter.parse(
            'API_v2', body, zone_transfer_request)

        zone_transfer_request.validate()

        zone_transfer_request = self.central_api.update_zone_transfer_request(
            context, zone_transfer_request)

        LOG.info(_LI("Updated %(zt_request)s"),
                 {'zt_request': zone_transfer_request})

        response.status_int = 200

        return DesignateAdapter.render(
            'API_v2', zone_transfer_request, request=request, context=context)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('zone_transfer_request_id')
    def delete_one(self, zone_transfer_request_id):
        """Delete ZoneTransferRequest"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        zone_transfer_request = self.central_api.delete_zone_transfer_request(
            context, zone_transfer_request_id)

        response.status_int = 204

        LOG.info(_LI("Deleted %(zone_transfer_request)s"),
                 {'zone_transfer_request': zone_transfer_request})

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
