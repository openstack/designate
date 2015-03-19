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

from designate.api.v2.controllers import rest
from designate.api.admin.controllers.extensions import counts
from designate.api.admin.controllers.extensions import tenants

LOG = logging.getLogger(__name__)


class ReportsController(rest.RestController):

    @staticmethod
    def get_path():
        return '.reports'

    counts = counts.CountsController()
    tenants = tenants.TenantsController()
