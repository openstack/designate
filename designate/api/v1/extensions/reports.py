# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Simon McCartney <simon.mccartney@hpe.com>
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
blueprint = flask.Blueprint('reports', __name__)


@blueprint.route('/reports/tenants', methods=['GET'])
def reports_tenants():
    context = flask.request.environ.get('context')

    tenants = central_api.find_tenants(context)

    return flask.jsonify(tenants=tenants)


@blueprint.route('/reports/tenants/<tenant_id>', methods=['GET'])
def reports_tenant(tenant_id):
    context = flask.request.environ.get('context')

    tenant = central_api.get_tenant(context, tenant_id)

    return flask.jsonify(tenant)


@blueprint.route('/reports/counts', methods=['GET'])
def reports_counts():
    context = flask.request.environ.get('context')

    tenants = central_api.count_tenants(context)
    domains = central_api.count_zones(context)
    records = central_api.count_records(context)

    return flask.jsonify(tenants=tenants, domains=domains, records=records)


@blueprint.route('/reports/counts/tenants', methods=['GET'])
def reports_counts_tenants():
    context = flask.request.environ.get('context')

    count = central_api.count_tenants(context)

    return flask.jsonify(tenants=count)


@blueprint.route('/reports/counts/domains', methods=['GET'])
def reports_counts_domains():
    context = flask.request.environ.get('context')

    count = central_api.count_zones(context)

    return flask.jsonify(domains=count)


@blueprint.route('/reports/counts/records', methods=['GET'])
def reports_counts_records():
    context = flask.request.environ.get('context')

    count = central_api.count_records(context)

    return flask.jsonify(records=count)
