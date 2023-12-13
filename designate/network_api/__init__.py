# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
from oslo_log import log

from designate.network_api import base


LOG = log.getLogger(__name__)

neutron_opts = [
    cfg.StrOpt('network_api', default='neutron', help='Which API to use.')
]

cfg.CONF.register_opts(neutron_opts)


def get_network_api(network_api_driver):
    LOG.debug('Loading network_api driver: %s', network_api_driver)

    cls = base.NetworkAPI.get_driver(network_api_driver)

    return cls()
