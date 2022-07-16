# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

from designate.api.v2.controllers import rest
from designate.objects.adapters import DesignateAdapter
from designate import utils


class ServiceStatusController(rest.RestController):
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'hostname', 'service_name',
                 'status']

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        request = pecan.request
        context = pecan.request.environ['context']

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
                context, params, self.SORT_KEYS)

        accepted_filters = ["hostname", "service_name", "status"]
        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        service_statuses = self.central_api.find_service_statuses(
            context, criterion, )

        return DesignateAdapter.render('API_v2', service_statuses,
                                       request=request)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('service_id')
    def get_one(self, service_id):
        """Get Service Status"""
        request = pecan.request
        context = request.environ['context']

        criterion = {"id": service_id}
        service_status = self.central_api.find_service_status(
            context, criterion)

        return DesignateAdapter.render('API_v2', service_status,
                                       request=request)
