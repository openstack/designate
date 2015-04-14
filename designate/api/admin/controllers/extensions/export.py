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

import pecan
from oslo_log import log as logging

from designate.api.v2.controllers import rest
from designate import utils
from designate import policy

LOG = logging.getLogger(__name__)


class ExportController(rest.RestController):

    @pecan.expose(template=None, content_type='text/dns')
    @utils.validate_uuid('zone_id')
    def get_one(self, zone_id):
        context = pecan.request.environ['context']

        policy.check('zone_export', context)

        servers = self.central_api.get_domain_servers(context, zone_id)
        domain = self.central_api.get_domain(context, zone_id)

        criterion = {'domain_id': zone_id}
        recordsets = self.central_api.find_recordsets(context, criterion)

        records = []

        for recordset in recordsets:
            criterion = {
                'domain_id': domain['id'],
                'recordset_id': recordset['id']
            }

            raw_records = self.central_api.find_records(context, criterion)

            for record in raw_records:
                records.append({
                    'name': recordset['name'],
                    'type': recordset['type'],
                    'ttl': recordset['ttl'],
                    'data': record['data'],
                })

        return utils.render_template('bind9-zone.jinja2',
                                     servers=servers,
                                     domain=domain,
                                     records=records)
