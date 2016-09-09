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

from designate import schema
from designate.central import rpcapi as central_rpcapi


blueprint = flask.Blueprint('limits', __name__)
limits_schema = schema.Schema('v1', 'limits')


@blueprint.route('/schemas/limits', methods=['GET'])
def get_limits_schema():
    return flask.jsonify(limits_schema.raw)


@blueprint.route('/limits', methods=['GET'])
def get_limits():
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    absolute_limits = central_api.get_absolute_limits(context)

    return flask.jsonify(limits_schema.filter({
        "limits": {
            "absolute": {
                "maxDomains": absolute_limits['zones'],
                "maxDomainRecords": absolute_limits['zone_records']
            }
        }
    }))
