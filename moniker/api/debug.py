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
from moniker.openstack.common import log as logging

LOG = logging.getLogger(__name__)

blueprint = flask.Blueprint('debug', __name__)


@blueprint.route('/config', methods=['GET'])
def list_config():
    return flask.jsonify(cfg.CONF)


@blueprint.route('/context', methods=['GET'])
def list_config():
    return flask.jsonify(flask.request.context.to_dict())
