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
import flask
from stevedore import extension
from stevedore import named
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging

LOG = logging.getLogger(__name__)

cfg.CONF.register_opts([
    cfg.ListOpt('enabled-extensions-v1', default=[],
                help='Enabled API Extensions'),
], group='service:api')


def factory(global_config, **local_conf):
    app = flask.Flask('moniker.api.v1')

    # TODO(kiall): Ideally, we want to make use of the Plugin class here.
    #              This works for the moment though.
    def _register_blueprint(ext):
        app.register_blueprint(ext.plugin)

    # Add all in-built APIs
    mgr = extension.ExtensionManager('moniker.api.v1')
    mgr.map(_register_blueprint)

    # Add any (enabled) optional extensions
    extensions = cfg.CONF['service:api'].enabled_extensions_v1

    if len(extensions) > 0:
        extmgr = named.NamedExtensionManager('moniker.api.v1.extensions',
                                             names=extensions)
        extmgr.map(_register_blueprint)

    return app
