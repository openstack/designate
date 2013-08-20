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
from designate.openstack.common import log as logging
from designate.api.v2.controllers import limits
from designate.api.v2.controllers import schemas
from designate.api.v2.controllers import zones

LOG = logging.getLogger(__name__)


class RootController(object):
    """
    This is /v2/ Controller. Pecan will find all controllers via the object
    properties attached to this.
    """
    limits = limits.LimitsController()
    schemas = schemas.SchemasController()
    zones = zones.ZonesController()
