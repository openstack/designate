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
from moniker.openstack.common.rpc import common as rpc_common
from moniker import exceptions
from moniker.central import rpcapi as central_rpcapi

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()
blueprint = flask.Blueprint('reports', __name__)


@blueprint.route('/reports', methods=['GET'])
def reports():
    context = flask.request.environ.get('context')

    try:
        domains = central_api.count_domains(context)
        records = central_api.count_records(context)
        tenants = central_api.count_tenants(context)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.DomainNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        return flask.jsonify(domains=int(domains), records=int(records),
                             tenants=int(tenants))


@blueprint.route('/reports/domains', methods=['GET'])
def reports_domains():
    context = flask.request.environ.get('context')

    try:
        count = central_api.count_domains(context)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.DomainNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        return flask.jsonify(domains=int(count))


@blueprint.route('/reports/records', methods=['GET'])
def reports_records():
    context = flask.request.environ.get('context')

    try:
        count = central_api.count_records(context)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.DomainNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        return flask.jsonify(records=int(count))


@blueprint.route('/reports/tenants', methods=['GET'])
def reports_tenants():
    context = flask.request.environ.get('context')

    try:
        count = central_api.count_tenants(context)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.DomainNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        LOG.debug(count)
        return flask.jsonify(tenants=int(count))
