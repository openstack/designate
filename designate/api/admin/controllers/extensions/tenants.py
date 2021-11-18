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
import pecan

from designate.api.admin.views.extensions import reports as reports_view
from designate.api.v2.controllers import rest

LOG = logging.getLogger(__name__)


class TenantsController(rest.RestController):

    _view = reports_view.TenantsView()

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self):
        request = pecan.request
        context = pecan.request.environ['context']

        tenants = self.central_api.find_tenants(context)

        return self._view.list(context, request, tenants)

    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, tenant_id):
        """Get Tenant"""
        request = pecan.request
        context = request.environ['context']

        tenant = self.central_api.get_tenant(context, tenant_id)

        return self._view.show_detail(context, request, tenant)
