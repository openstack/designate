# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from oslo_config import cfg
from stevedore import named

from designate.api.v2.controllers import limits
from designate.api.v2.controllers import reverse
from designate.api.v2.controllers import tlds
from designate.api.v2.controllers import blacklists
from designate.api.v2.controllers import errors
from designate.api.v2.controllers import pools
from designate.api.v2.controllers import service_status
from designate.api.v2.controllers import zones
from designate.api.v2.controllers import tsigkeys
from designate.api.v2.controllers import recordsets
from designate.api.v2.controllers import quotas


class RootController(object):
    """
    This is /v2/ Controller. Pecan will find all controllers via the object
    properties attached to this.
    """

    def __init__(self):
        enabled_ext = cfg.CONF['service:api'].enabled_extensions_v2
        if len(enabled_ext) > 0:
            self._mgr = named.NamedExtensionManager(
                namespace='designate.api.v2.extensions',
                names=enabled_ext,
                invoke_on_load=True)
            for ext in self._mgr:
                controller = self
                path = ext.obj.get_path()
                for p in path.split('.')[:-1]:
                    if p != '':
                        controller = getattr(controller, p)
                setattr(controller, path.split('.')[-1], ext.obj)

    limits = limits.LimitsController()
    reverse = reverse.ReverseController()
    tlds = tlds.TldsController()
    zones = zones.ZonesController()
    blacklists = blacklists.BlacklistsController()
    errors = errors.ErrorsController()
    pools = pools.PoolsController()
    service_statuses = service_status.ServiceStatusController()
    tsigkeys = tsigkeys.TsigKeysController()
    recordsets = recordsets.RecordSetsViewController()
    quotas = quotas.QuotasController()
