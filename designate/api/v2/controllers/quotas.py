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
import pecan
from oslo_log import log as logging

from designate.api.v2.controllers import rest
from designate.objects.adapters import DesignateAdapter
from designate.objects import QuotaList

LOG = logging.getLogger(__name__)


class QuotasController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self):
        context = pecan.request.environ['context']

        quotas = self.central_api.get_quotas(context, context.tenant)

        quotas = QuotaList.from_dict(quotas)

        return DesignateAdapter.render('API_v2', quotas)

    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, tenant_id):
        context = pecan.request.environ['context']

        quotas = self.central_api.get_quotas(context, tenant_id)

        quotas = QuotaList.from_dict(quotas)

        return DesignateAdapter.render('API_v2', quotas)

    @pecan.expose(template='json:', content_type='application/json')
    def patch_one(self, tenant_id):
        """Modify a Quota"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict

        quotas = DesignateAdapter.parse('API_v2', body, QuotaList())

        for quota in quotas:
            self.central_api.set_quota(context, tenant_id, quota.resource,
                                       quota.hard_limit)

        quotas = self.central_api.get_quotas(context, tenant_id)

        quotas = QuotaList.from_dict(quotas)

        return DesignateAdapter.render('API_v2', quotas)

    @pecan.expose(template=None, content_type='application/json')
    def delete_one(self, tenant_id):
        """Reset to the Default Quotas"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.reset_quotas(context, tenant_id)

        response.status_int = 204

        return ''
