# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from oslo_log import log as logging
from stevedore import named

from designate.api.v2.controllers import errors
import designate.conf


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class RootController:
    """
    This is /admin/ Controller. Pecan will find all controllers via the object
    properties attached to this.
    """

    def __init__(self):
        enabled_ext = CONF['service:api'].enabled_extensions_admin
        if len(enabled_ext) > 0:
            self._mgr = named.NamedExtensionManager(
                namespace='designate.api.admin.extensions',
                names=enabled_ext,
                invoke_on_load=True)
            for ext in self._mgr:
                controller = self
                path = ext.obj.get_path()
                LOG.info("Registering an API extension at path %s", path)
                for p in path.split('.')[:-1]:
                    if p != '':
                        controller = getattr(controller, p)
                setattr(controller, path.split('.')[-1], ext.obj)

    errors = errors.ErrorsController()
