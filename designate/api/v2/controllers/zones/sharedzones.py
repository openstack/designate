# Copyright 2020 Cloudification GmbH. All rights reserved.
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
import pecan

from designate.api.v2.controllers import rest
from designate.common import keystone
from designate.objects.adapters import DesignateAdapter
from designate.objects import SharedZone
from designate import utils

LOG = logging.getLogger(__name__)


class SharedZonesController(rest.RestController):
    SORT_KEYS = ['created_at', 'updated_at', ]

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'zone_share_id')
    def get_one(self, zone_id, zone_share_id):
        """Get Zone Share"""
        request = pecan.request
        context = request.environ['context']

        zone = self.central_api.get_shared_zone(
                context, zone_id, zone_share_id)

        LOG.info(
            "Retrieved %(zone)s",
            {"zone": zone}
        )

        return DesignateAdapter.render('API_v2', zone, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def get_all(self, zone_id, **params):
        """List all Shared Zones"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params, self.SORT_KEYS)

        # Extract any filter params
        accepted_filters = ('target_project_id',)
        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        criterion['zone_id'] = zone_id

        shared_zones = self.central_api.find_shared_zones(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info("Retrieved %(shared_zones)s", {'shared_zones': shared_zones})

        return DesignateAdapter.render('API_v2', shared_zones, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Share Zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        payload = request.body_dict

        keystone.verify_project_id(
            context, payload.get('target_project_id', None)
        )

        zone_share = DesignateAdapter.parse('API_v2', payload, SharedZone())

        zone_share = self.central_api.share_zone(context, zone_id, zone_share)

        response.status_int = 201

        LOG.info(
            "Shared %(shared_zone)s",
            {'shared_zone': zone_share}
        )

        return DesignateAdapter.render(
            'API_v2', zone_share, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'zone_share_id')
    def delete_one(self, zone_id, zone_share_id):
        """Unshare Zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        zone = self.central_api.unshare_zone(context, zone_id, zone_share_id)
        response.status_int = 204

        LOG.info("Unshared %(zone)s", {'zone': zone})
