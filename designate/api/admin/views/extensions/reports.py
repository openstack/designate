# COPYRIGHT 2014 Rackspace
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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


class CountsView(base_view.BaseView):
    """View for the Counts Reports"""

    _resource_name = 'reports'
    _collection_name = 'reports'

    def show(self, context, request, counts):
        """Basic view of the Counts Reports"""

        return {
                "counts": counts
        }


class TenantsView(base_view.BaseView):
    """View for the Tenants Reports"""

    _resource_name = 'tenants'
    _collection_name = 'tenants'

    def _get_base_href(self, parents=None):

        href = "%s/v2/reports/tenants" % (self.base_uri)

        return href.rstrip('?')

    def show_basic(self, context, request, tenants):
        """Basic view of the Tenants Report"""

        return {
            "zone_count": tenants['domain_count'],
            "id": tenants['id'],
            "links": self._get_resource_links(request, tenants)
        }

    def show_detail(self, context, request, tenant):
        """Detail view of the Tenants Report"""

        return {
            "zones_count": tenant['domain_count'],
            "zones": tenant['domains'],
            "id": tenant['id'],
            "links": self._get_resource_links(request, tenant)
        }
