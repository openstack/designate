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
from designate.api.v2.views import base as base_view
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class LimitsView(base_view.BaseView):
    """Model a Limits API response as a python dictionary"""

    _resource_name = 'limits'
    _collection_name = 'limits'

    def show_basic(self, context, request, absolute_limits):
        """Basic view of the limits"""

        return {
            "absolute": {
                "max_zones": absolute_limits['domains'],
                "max_zone_recordsets": absolute_limits['domain_recordsets'],
                "max_zone_records": absolute_limits['domain_records'],
                "max_recordset_records": absolute_limits['recordset_records']
            }
        }
