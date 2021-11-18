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
import pecan

from designate.api.admin.views.extensions import quotas as quotas_view
from designate.api.v2.controllers import rest
from designate import schema

LOG = logging.getLogger(__name__)


class QuotasController(rest.RestController):
    _view = quotas_view.QuotasView()
    _resource_schema = schema.Schema('admin', 'quota')

    @staticmethod
    def get_path():
        return '.quotas'

    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, tenant_id):
        request = pecan.request
        context = pecan.request.environ['context']
        context.all_tenants = True

        quotas = self.central_api.get_quotas(context, tenant_id)

        return self._view.show(context, request, quotas)

    @pecan.expose(template='json:', content_type='application/json')
    def patch_one(self, tenant_id):
        """Modify a Quota"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        context.all_tenants = True
        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        values = self._view.load(context, request, body)

        for resource, hard_limit in values.items():
            self.central_api.set_quota(context, tenant_id, resource,
                                       hard_limit)

        response.status_int = 200

        quotas = self.central_api.get_quotas(context, tenant_id)

        return self._view.show(context, request, quotas)

    @pecan.expose(template=None, content_type='application/json')
    def delete_one(self, tenant_id):
        """Reset to the Default Quotas"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        context.all_tenants = True

        self.central_api.reset_quotas(context, tenant_id)

        response.status_int = 204

        return ''
