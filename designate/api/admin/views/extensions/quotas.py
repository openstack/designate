# COPYRIGHT 2014 Rackspace
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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

from designate.api.admin.views import base as base_view


LOG = logging.getLogger(__name__)


class QuotasView(base_view.BaseView):
    """Model a Quota API response as a python dictionary"""

    _resource_name = 'quota'
    _collection_name = 'quotas'

    def show_basic(self, context, request, quota):
        """Basic view of a quota"""
        return {
            "zones": quota['domains'],
            "zone_records": quota['domain_records'],
            "zone_recordsets": quota['domain_recordsets'],
            "recordset_records": quota['recordset_records']
        }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('domain_records', 'domain_recordsets', 'domains',
                      'recordset_records')

        quota = body["quota"]

        old_keys = {
            'zones': 'domains',
            'zone_records': 'domain_records',
            'zone_recordsets': 'domain_recordsets',
            'recordset_records': 'recordset_records'
        }

        for key in quota:
            quota[old_keys[key]] = quota.pop(key)

        return self._load(context, request, body, valid_keys)
