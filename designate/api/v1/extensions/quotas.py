# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from designate.openstack.common import log as logging
from designate.central import rpcapi as central_rpcapi

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()
blueprint = flask.Blueprint('quotas', __name__)


@blueprint.route('/quotas/<tenant_id>', methods=['GET'])
def get_quotas(tenant_id):
    context = flask.request.environ.get('context')

    quotas = central_api.get_quotas(context, tenant_id)

    return flask.jsonify(quotas)


@blueprint.route('/quotas/<tenant_id>', methods=['PUT', 'POST'])
def set_quota(tenant_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    for resource, hard_limit in values.items():
        central_api.set_quota(context, tenant_id, resource, hard_limit)

    quotas = central_api.get_quotas(context, tenant_id)
    return flask.jsonify(quotas)


@blueprint.route('/quotas/<tenant_id>', methods=['DELETE'])
def reset_quotas(tenant_id):
    context = flask.request.environ.get('context')

    central_api.reset_quotas(context, tenant_id)

    return flask.Response(status=200)
