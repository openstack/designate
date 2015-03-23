# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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

from designate.api.v2.controllers import rest


LOG = logging.getLogger(__name__)


class LimitsController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self):
        context = pecan.request.environ['context']

        absolute_limits = self.central_api.get_absolute_limits(context)

        return {
            "max_zones": absolute_limits['domains'],
            "max_zone_recordsets": absolute_limits['domain_recordsets'],
            "max_zone_records": absolute_limits['domain_records'],
            "max_recordset_records": absolute_limits['recordset_records']
        }
