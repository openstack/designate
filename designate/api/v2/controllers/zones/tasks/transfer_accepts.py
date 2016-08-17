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
from designate.api.v2.controllers import rest
from designate.objects import ZoneTransferAccept
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI


LOG = logging.getLogger(__name__)


class TransferAcceptsController(rest.RestController):

    SORT_KEYS = ['created_at', 'id', 'updated_at']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('transfer_accept_id')
    def get_one(self, transfer_accept_id):
        """Get transfer_accepts"""

        request = pecan.request
        context = request.environ['context']

        transfer_accepts = self.central_api.get_zone_transfer_accept(
            context, transfer_accept_id)

        LOG.info(_LI("Retrieved %(transfer_accepts)s"),
                 {'transfer_accepts': transfer_accepts})

        return DesignateAdapter.render(
            'API_v2', transfer_accepts, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List ZoneTransferAccepts"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params, self.SORT_KEYS)

        # Extract any filter params.
        criterion = self._apply_filter_params(params, ('status',), {})

        zone_transfer_accepts = self.central_api.find_zone_transfer_accepts(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info(_LI("Retrieved %(zone_transfer_accepts)s"),
                 {'zone_transfer_accepts': zone_transfer_accepts})

        return DesignateAdapter.render(
            'API_v2',
            zone_transfer_accepts,
            request=request,
            context=context)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create ZoneTransferAccept"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        zone_transfer_accept = DesignateAdapter.parse(
            'API_v2', body, ZoneTransferAccept())

        zone_transfer_accept.validate()

        # Create the zone_transfer_request
        zone_transfer_accept = self.central_api.create_zone_transfer_accept(
            context, zone_transfer_accept)
        response.status_int = 201

        LOG.info(_LI("Created %(zone_transfer_accept)s"),
                 {'zone_transfer_accept': zone_transfer_accept})

        zone_transfer_accept = DesignateAdapter.render(
            'API_v2', zone_transfer_accept, request=request)

        response.headers['Location'] = zone_transfer_accept['links']['self']

        # Prepare and return the response body
        return zone_transfer_accept
