# Copyright 2022 Cloudification GmbH
#
# Author: Kiran P <contact@cloudification.io>
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
from designate import exceptions
from designate.objects.adapters import DesignateAdapter
from designate import utils

LOG = logging.getLogger(__name__)


class PoolMoveController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Move a zone"""
        request = pecan.request
        response = pecan.response
        body = request.body_dict
        context = request.environ['context']

        zone = self.central_api.get_zone(context, zone_id)

        if zone.action == "DELETE":
            raise exceptions.BadRequest('Can not move a deleting zone')

        target_pool_id = None
        if 'pool_id' in body:
            if zone.pool_id == body['pool_id']:
                raise exceptions.BadRequest(
                    'Target pool must be different for zone pool move'
                )
            target_pool_id = body['pool_id']

        # Update the zone object with the new values
        zone = DesignateAdapter.parse('API_v2', body, zone)
        zone.validate()

        LOG.info('Triggered pool move for %(zone)s', {'zone': zone})
        zone = self.central_api.pool_move_zone(
            context, zone_id, target_pool_id
        )
        if zone.status == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 500

        return ''
