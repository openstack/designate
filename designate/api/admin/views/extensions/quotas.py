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
            "api_export_size": quota['api_export_size'],
            "zones": quota['zones'],
            "zone_records": quota['zone_records'],
            "zone_recordsets": quota['zone_recordsets'],
            "recordset_records": quota['recordset_records']
        }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('zone_records', 'zone_recordsets', 'zones',
                      'recordset_records', 'api_export_size')

        return self._load(context, request, body, valid_keys)
