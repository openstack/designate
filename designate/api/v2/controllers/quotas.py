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

from designate.api.v2.controllers import rest
from designate.common import keystone
import designate.conf
from designate import exceptions
from designate.objects.adapters import DesignateAdapter
from designate.objects import QuotaList


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class QuotasController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self):
        context = pecan.request.environ['context']

        quotas = self.central_api.get_quotas(context, context.project_id)

        quotas = QuotaList.from_dict(quotas)

        return DesignateAdapter.render('API_v2', quotas)

    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, project_id):
        context = pecan.request.environ['context']

        quotas = self.central_api.get_quotas(context, project_id)

        quotas = QuotaList.from_dict(quotas)

        return DesignateAdapter.render('API_v2', quotas)

    @pecan.expose(template='json:', content_type='application/json')
    def patch_one(self, project_id):
        """Modify a Quota"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict

        # NOTE(pas-ha) attempting to verify the validity of the project-id
        # on a best effort basis
        # this will raise only if KeystoneV3 endpoint is not found at all,
        # or the creds are passing but the project is not found
        if CONF['service:api'].quotas_verify_project_id:
            keystone.verify_project_id(context, project_id)

        quotas = DesignateAdapter.parse('API_v2', body, QuotaList())

        # The get_quotas lookup will always return the default quotas
        # if the context does not have a project_id (system scoped token) and
        # the all_tenants boolean is false. Let's require all_tenants for
        # contexts with no project ID.
        if context.project_id is None and not context.all_tenants:
            raise exceptions.MissingProjectID(
                "The all-projects flag must be used when using non-project "
                "scoped tokens."
            )

        for quota in quotas:
            self.central_api.set_quota(context, project_id, quota.resource,
                                       quota.hard_limit)

        quotas = self.central_api.get_quotas(context, project_id)

        quotas = QuotaList.from_dict(quotas)

        return DesignateAdapter.render('API_v2', quotas)

    @pecan.expose(template=None, content_type='application/json')
    def delete_one(self, project_id):
        """Reset to the Default Quotas"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.reset_quotas(context, project_id)

        response.status_int = 204

        return ''
