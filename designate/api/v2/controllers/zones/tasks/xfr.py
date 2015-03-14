# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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

from designate import utils
from designate.api.v2.controllers import rest


class XfrController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """XFR a zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.perform_zone_xfr(context, zone_id)
        response.status_int = 202

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
