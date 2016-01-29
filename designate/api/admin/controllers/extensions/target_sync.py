# COPYRIGHT 2015 Rackspace Inc.
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
from oslo_config import cfg

from designate.api.v2.controllers import rest
from designate import exceptions

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class TargetSyncController(rest.RestController):

    @staticmethod
    def get_path():
        return '.target_sync'

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Initialize a Target Syncing"""
        request = pecan.request
        context = request.environ['context']

        body = request.body_dict

        fields = ['target_id', 'timestamp']
        for f in fields:
            if f not in body:
                raise exceptions.BadRequest('Failed to supply correct fields')

        if (not isinstance(body['timestamp'], int) or body['timestamp'] < 0):
            raise exceptions.BadRequest(
                'Timestamp should be a positive integer')

        pool_id = CONF['service:pool_manager'].pool_id

        return {
            'message': self.pool_mgr_api.target_sync(context, pool_id,
            body['target_id'], body['timestamp'])
        }
