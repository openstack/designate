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
import flask

from designate.central import rpcapi as central_rpcapi


central_api = central_rpcapi.CentralAPI()
blueprint = flask.Blueprint('touch', __name__)


@blueprint.route('/domains/<uuid:domain_id>/touch', methods=['POST'])
def touch_domain(domain_id):
    context = flask.request.environ.get('context')

    central_api.touch_zone(context, domain_id)

    return flask.Response(status=200)
