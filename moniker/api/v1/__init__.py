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
from moniker.api.v1.domains import blueprint as domains_blueprint
from moniker.api.v1.records import blueprint as records_blueprint
from moniker.api.v1.servers import blueprint as servers_blueprint
from moniker.api.v1.tsigkeys import blueprint as tsigkeys_blueprint


def factory(global_config, **local_conf):
    app = flask.Flask('moniker.api.v1')

    app.register_blueprint(domains_blueprint)
    app.register_blueprint(records_blueprint)
    app.register_blueprint(servers_blueprint)
    app.register_blueprint(tsigkeys_blueprint)

    return app
