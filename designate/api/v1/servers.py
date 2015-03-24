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
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import schema
from designate import objects
from designate.i18n import _LI
from designate.central import rpcapi as central_rpcapi


LOG = logging.getLogger(__name__)
blueprint = flask.Blueprint('servers', __name__)
server_schema = schema.Schema('v1', 'server')
servers_schema = schema.Schema('v1', 'servers')
default_pool_id = cfg.CONF['service:central'].default_pool_id

# Servers are no longer used. They have been replaced by nameservers, which
# is stored as a PoolAttribute. However, the v1 server API calls still need
# to work


def _pool_ns_record_to_server(pool_ns_record):
    server_values = {
        'id': pool_ns_record.id,
        'created_at': pool_ns_record.created_at,
        'updated_at': pool_ns_record.updated_at,
        'version': pool_ns_record.version,
        'name': pool_ns_record.hostname
    }

    return objects.Server.from_dict(server_values)


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

    # Create a PoolNsRecord object
    pns_values = {
        'priority': 10,
        'hostname': values['name']
    }
    ns_record = objects.PoolNsRecord.from_dict(pns_values)

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)

    # Add the new PoolAttribute to the pool as a nameserver
    pool.ns_records.append(ns_record)

    try:
        # Update the pool
        updated_pool = central_api.update_pool(context, pool)
        LOG.info(_LI("Updated %(pool)s"), {'pool': pool})

    except exceptions.DuplicatePoolAttribute:
        raise exceptions.DuplicateServer()

    # Go through the pool.ns_records to find the right one to get the ID
    for ns in updated_pool.ns_records:
        if ns.hostname == pns_values['hostname']:
            created_ns_record = ns
            break

    # Convert the PoolAttribute to a Server so we can validate with the
    # original schema and display
    server = _pool_ns_record_to_server(created_ns_record)

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
    LOG.info(_LI("Retrieved %(pool)s"), {'pool': pool})

    servers = objects.ServerList()

    for ns in pool.ns_records:
        servers.append(_pool_ns_record_to_server(ns))

    LOG.info(_LI("Retrieved %(servers)s"), {'servers': servers})

    return flask.jsonify(servers_schema.filter({'servers': servers}))


@blueprint.route('/servers/<uuid:server_id>', methods=['GET'])
def get_server(server_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)
    LOG.info(_LI("Retrieved %(pool)s"), {'pool': pool})

    # Create an empty PoolNsRecord object
    nameserver = objects.PoolNsRecord()

    # Get the desired nameserver from the pool
    for ns in pool.ns_records:
        if ns.id == server_id:
            nameserver = ns
            break

    # If the nameserver wasn't found, raise an exception
    if nameserver.id != server_id:
        raise exceptions.ServerNotFound

    LOG.info(_LI("Retrieved %(server)s"), {'server': nameserver})

    server = _pool_ns_record_to_server(nameserver)

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
    ns_records = pool.ns_records
    for ns in ns_records:
        if ns.id == server_id:
            index = ns_records.index(ns)
            break

    if index == -1:
        raise exceptions.ServerNotFound

    # Get the ns_record from the pool so we can update it
    nameserver = ns_records.pop(index)

    # Update it with the new values
    nameserver.update({'hostname': values['name']})

    # Change it to a server, so we can use the original validation. We want
    # to make sure we don't change anything in v1
    server = _pool_ns_record_to_server(nameserver)
    server_data = server_schema.filter(server)
    server_data.update(values)
    # Validate the new set of data
    server_schema.validate(server_data)

    # Now that it's been validated, add it back to the pool and persist it
    pool.ns_records.append(nameserver)
    pool = central_api.update_pool(context, pool)
    LOG.info(_LI("Updated %(pool)s"), {'pool': pool})

    return flask.jsonify(server_schema.filter(server))


@blueprint.route('/servers/<uuid:server_id>', methods=['DELETE'])
def delete_server(server_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Get the default pool
    pool = central_api.get_pool(context, default_pool_id)

    # Get the Nameserver from the pool
    index = -1
    ns_records = pool.ns_records
    for ns in ns_records:
        if ns.id == server_id:
            index = ns_records.index(ns)
            break

    if index == -1:
        raise exceptions.ServerNotFound

    # Remove the nameserver from the pool so it will be deleted
    ns_records.pop(index)

    # Update the pool without the deleted server
    pool = central_api.update_pool(context, pool)
    LOG.info(_LI("Updated %(pool)s"), {'pool': pool})

    return flask.Response(status=200)
