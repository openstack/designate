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
from oslo.config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import schema
from designate import objects
from designate.central import rpcapi as central_rpcapi


LOG = logging.getLogger(__name__)
blueprint = flask.Blueprint('servers', __name__)
server_schema = schema.Schema('v1', 'server')
servers_schema = schema.Schema('v1', 'servers')
default_pool_id = cfg.CONF['service:central'].default_pool_id

# Servers are no longer used. They have been replaced by nameservers, which
# is stored as a PoolAttribute. However, the v1 server API calls still need
# to work


def _poolattribute_to_server(pool_attribute):
    server_values = {
        'id': pool_attribute.id,
        'created_at': pool_attribute.created_at,
        'updated_at': pool_attribute.updated_at,
        'version': pool_attribute.version,
        'name': pool_attribute.value
    }

    server = objects.Server(**server_values)
    return server


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
    central_api = central_rpcapi.CentralAPI.get_instance()
    # Validate against the original server schema
    server_schema.validate(values)

    # Create a PoolAttribute object
    pa_values = {
        'pool_id': default_pool_id,
        'key': 'name_server',
        'value': values['name']
    }
    nameserver = objects.NameServer(**pa_values)

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)

    # Add the new PoolAttribute to the pool as a nameserver
    pool.nameservers.append(nameserver)

    try:
        # Update the pool
        updated_pool = central_api.update_pool(context, pool)

    except exceptions.DuplicatePoolAttribute:
        raise exceptions.DuplicateServer()

    # Go through the pool.nameservers to find the right one to get the ID
    for ns in updated_pool.nameservers:
        if ns.value == pa_values['value']:
            created_nameserver = ns
            break

    # Convert the PoolAttribute to a Server so we can validate with the
    # original schema and display
    server = _poolattribute_to_server(created_nameserver)

    response = flask.jsonify(server_schema.filter(server))
    response.status_int = 201
    response.location = flask.url_for('.get_server', server_id=server['id'])

    return response


@blueprint.route('/servers', methods=['GET'])
def get_servers():
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)

    servers = objects.ServerList()

    for ns in pool.nameservers:
        servers.append(_poolattribute_to_server(ns))

    return flask.jsonify(servers_schema.filter({'servers': servers}))


@blueprint.route('/servers/<uuid:server_id>', methods=['GET'])
def get_server(server_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)

    # Create an empty PoolAttribute object
    nameserver = objects.NameServer()

    # Get the desired nameserver from the pool
    for ns in pool.nameservers:
        if ns.id == server_id:
            nameserver = ns
            break

    # If the nameserver wasn't found, raise an exception
    if nameserver.id != server_id:
        raise exceptions.ServerNotFound

    server = _poolattribute_to_server(nameserver)

    return flask.jsonify(server_schema.filter(server))


@blueprint.route('/servers/<uuid:server_id>', methods=['PUT'])
def update_server(server_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)

    # Get the Nameserver from the pool
    index = -1
    nameservers = pool.nameservers
    for ns in nameservers:
        if ns.id == server_id:
            index = nameservers.index(ns)
            break

    if index == -1:
        raise exceptions.ServerNotFound

    # Get the nameserver from the pool so we can update it
    nameserver = nameservers.pop(index)

    # Update it with the new values
    nameserver.update({'value': values['name']})

    # Change it to a server, so we can use the original validation. We want
    # to make sure we don't change anything in v1
    server = _poolattribute_to_server(nameserver)
    server_data = server_schema.filter(server)
    server_data.update(values)
    # Validate the new set of data
    server_schema.validate(server_data)

    # Now that it's been validated, add it back to the pool and persist it
    pool.nameservers.append(nameserver)
    central_api.update_pool(context, pool)

    return flask.jsonify(server_schema.filter(server))


@blueprint.route('/servers/<uuid:server_id>', methods=['DELETE'])
def delete_server(server_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)

    # Get the Nameserver from the pool
    index = -1
    nameservers = pool.nameservers
    for ns in nameservers:
        if ns.id == server_id:
            index = nameservers.index(ns)
            break

    if index == -1:
        raise exceptions.ServerNotFound

    # Remove the nameserver from the pool so it will be deleted
    nameservers.pop(index)

    # Update the pool without the deleted server
    central_api.update_pool(context, pool)

    return flask.Response(status=200)
