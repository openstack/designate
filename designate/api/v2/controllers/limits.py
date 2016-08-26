# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from oslo_config import cfg

from designate.api.v2.controllers import rest


CONF = cfg.CONF


class LimitsController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self):
        context = pecan.request.environ['context']

        absolute_limits = self.central_api.get_absolute_limits(context)

        return {
            # Resource Creation Limits
            "max_zones": absolute_limits['zones'],
            "max_zone_recordsets": absolute_limits['zone_recordsets'],
            "max_zone_records": absolute_limits['zone_records'],
            "max_recordset_records": absolute_limits['recordset_records'],

            # Resource Field Value Limits
            "min_ttl": CONF['service:central'].min_ttl,
            "max_zone_name_length":
                CONF['service:central'].max_zone_name_len,
            "max_recordset_name_length":
                CONF['service:central'].max_recordset_name_len,

            # Resource Fetching Limits
            "max_page_limit": CONF['service:api'].max_limit_v2,
        }
