# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Simon McCartney <simon.mccartney@hp.com>
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
from moniker.openstack.common import log as logging
from moniker.central import rpcapi as central_rpcapi

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()
blueprint = flask.Blueprint('reports', __name__)


@blueprint.route('/reports/counts', methods=['GET'])
def reports():
    context = flask.request.environ.get('context')

    domains = central_api.count_domains(context)
    records = central_api.count_records(context)
    tenants = central_api.count_tenants(context)

    return flask.jsonify(domains=domains, records=records, tenants=tenants)


@blueprint.route('/reports/counts/domains', methods=['GET'])
def reports_domains():
    context = flask.request.environ.get('context')

    count = central_api.count_domains(context)

    return flask.jsonify(domains=count)


@blueprint.route('/reports/counts/records', methods=['GET'])
def reports_records():
    context = flask.request.environ.get('context')

    count = central_api.count_records(context)

    return flask.jsonify(records=count)


@blueprint.route('/reports/counts/tenants', methods=['GET'])
def reports_tenants():
    context = flask.request.environ.get('context')

    count = central_api.count_tenants(context)

    return flask.jsonify(tenants=count)
