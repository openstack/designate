# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
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
import flask
import oslo_messaging as messaging

from designate import rpc


blueprint = flask.Blueprint('diagnostics', __name__)


@blueprint.route('/diagnostics/ping/<topic>/<host>', methods=['GET'])
def ping_host(topic, host):
    context = flask.request.environ.get('context')

    client = rpc.get_client(messaging.Target(topic=topic))
    cctxt = client.prepare(server=host, timeout=10)

    pong = cctxt.call(context, 'ping')

    return flask.jsonify(pong)
