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
from moniker.openstack.common import cfg
from moniker.openstack.common import jsonutils
from moniker.openstack.common.context import RequestContext
from moniker import central
from moniker.api import v1
from moniker.api import debug

# Allows us to serialize datetime's etc
flask.helpers.json = jsonutils

cfg.CONF.register_opts([
    cfg.StrOpt('api_host', default='0.0.0.0',
               help='API Host'),
    cfg.IntOpt('api_port', default=9001,
               help='API Port Number'),
])

app = flask.Flask('moniker.api')

# Blueprints
app.register_blueprint(v1.blueprint, url_prefix='/v1')
app.register_blueprint(debug.blueprint, url_prefix='/debug')


@app.before_request
def attach_context():
    request = flask.request
    headers = request.headers

    if cfg.CONF.enable_keystone:
        request.context = RequestContext(auth_tok=headers.get('X-Auth-Token'),
                                         user=headers.get('X-User-ID'),
                                         tenant=headers.get('X-Tenant-ID'))
    else:
        request.context = RequestContext(user=cfg.CONF.default_user,
                                         tenant=cfg.CONF.default_tenant)
