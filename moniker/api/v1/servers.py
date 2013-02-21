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
from moniker.openstack.common import log as logging
from moniker.openstack.common import jsonutils as json
from moniker.openstack.common.rpc import common as rpc_common
from moniker import exceptions
from moniker import schema
from moniker.central import api as central_api

LOG = logging.getLogger(__name__)
blueprint = flask.Blueprint('servers', __name__)
server_schema = schema.Schema('v1', 'server')
servers_schema = schema.Schema('v1', 'servers')


@blueprint.route('/schemas/server', methods=['GET'])
def get_server_schema():
    return flask.jsonify(server_schema.raw)


@blueprint.route('/schemas/servers', methods=['GET'])
def get_servers_schema():
    return flask.jsonify(servers_schema.raw)


@blueprint.route('/servers', methods=['POST'])
def create_server():
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        server_schema.validate(values)
        server = central_api.create_server(context, values=flask.request.json)
    except exceptions.InvalidObject, e:
        response_body = json.dumps({'errors': e.errors})
        return flask.Response(status=400, response=response_body)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.DuplicateServer:
        return flask.Response(status=409)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        server = server_schema.filter(server)

        response = flask.jsonify(server)
        response.status_int = 201
        response.location = flask.url_for('.get_server',
                                          server_id=server['id'])
        return response


@blueprint.route('/servers', methods=['GET'])
def get_servers():
    context = flask.request.environ.get('context')

    try:
        servers = central_api.get_servers(context)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        servers = servers_schema.filter({'servers': servers})

        return flask.jsonify(servers)


@blueprint.route('/servers/<server_id>', methods=['GET'])
def get_server(server_id):
    context = flask.request.environ.get('context')

    try:
        server = central_api.get_server(context, server_id)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.ServerNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        server = server_schema.filter(server)

        return flask.jsonify(server)


@blueprint.route('/servers/<server_id>', methods=['PUT'])
def update_server(server_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        server = central_api.get_server(context, server_id)
        server.update(values)

        server_schema.validate(server)
        server = central_api.update_server(context, server_id, values=values)
    except exceptions.InvalidObject, e:
        response_body = json.dumps({'errors': e.errors})
        return flask.Response(status=400, response=response_body)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.ServerNotFound:
        return flask.Response(status=404)
    except exceptions.DuplicateServer:
        return flask.Response(status=409)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        server = server_schema.filter(server)

        return flask.jsonify(server)


@blueprint.route('/servers/<server_id>', methods=['DELETE'])
def delete_server(server_id):
    context = flask.request.environ.get('context')

    try:
        central_api.delete_server(context, server_id)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.ServerNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        return flask.Response(status=200)
