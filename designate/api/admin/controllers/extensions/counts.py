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


class CountsController(rest.RestController):

    _view = reports_view.CountsView()

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self):
        request = pecan.request
        context = pecan.request.environ['context']

        counts = self.central_api.count_report(context)

        return self._view.show(context, request, counts)

    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, criterion):
        request = pecan.request
        context = pecan.request.environ['context']

        counts = self.central_api.count_report(context, criterion=criterion)

        return self._view.show(context, request, counts)
