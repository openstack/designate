# COPYRIGHT 2015 Hewlett-Packard Development Company, L.P.
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
from designate import policy
from designate import utils

LOG = logging.getLogger(__name__)


class ExportController(rest.RestController):

    @pecan.expose(template=None, content_type='text/dns')
    @utils.validate_uuid('zone_id')
    def get_one(self, zone_id):
        context = pecan.request.environ['context']
        policy.check('zone_export', context)

        zones = self.central_api.export_zone(context, zone_id)

        return zones
