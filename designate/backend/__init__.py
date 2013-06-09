# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from designate.plugin import Plugin

LOG = logging.getLogger(__name__)


def get_backend(backend_driver, central_service):
    LOG.debug("Loading backend driver: %s" % backend_driver)

    invoke_kwds = {
        'central_service': central_service
    }

    return Plugin.get_plugin(backend_driver, ns=__name__, invoke_on_load=True,
                             invoke_kwds=invoke_kwds)
