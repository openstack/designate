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
from oslo_log import log as logging

from designate import schema
from designate.api.v1 import load_values
from designate.central import rpcapi as central_rpcapi
from designate.i18n import _LI
from designate import objects


LOG = logging.getLogger(__name__)
blueprint = flask.Blueprint('domains', __name__)
domain_schema = schema.Schema('v1', 'domain')
domains_schema = schema.Schema('v1', 'domains')
servers_schema = schema.Schema('v1', 'servers')


def _pool_ns_record_to_server(pool_ns_record):
    server_values = {
        'id': pool_ns_record.id,
        'created_at': pool_ns_record.created_at,
        'updated_at': pool_ns_record.updated_at,
        'version': pool_ns_record.version,
        'name': pool_ns_record.hostname
    }

    return objects.Server.from_dict(server_values)


@blueprint.route('/schemas/domain', methods=['GET'])
def get_domain_schema():
    return flask.jsonify(domain_schema.raw)


@blueprint.route('/schemas/domains', methods=['GET'])
def get_domains_schema():
    return flask.jsonify(domains_schema.raw)


@blueprint.route('/domains', methods=['POST'])
def create_domain():
    valid_attributes = ['name', 'email', 'ttl', 'description']
    context = flask.request.environ.get('context')

    values = load_values(flask.request, valid_attributes)

    domain_schema.validate(values)

    central_api = central_rpcapi.CentralAPI.get_instance()

    # A V1 zone only supports being a primary (No notion of a type)
    values['type'] = 'PRIMARY'

    domain = central_api.create_zone(context, objects.Zone(**values))

    LOG.info(_LI("Created %(zone)s"), {'zone': domain})

    response = flask.jsonify(domain_schema.filter(domain))
    response.status_int = 201
    response.location = flask.url_for('.get_domain', domain_id=domain['id'])

    return response


@blueprint.route('/domains', methods=['GET'])
def get_domains():
    """List existing zones except those flagged for deletion
    """
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    domains = central_api.find_zones(context, criterion={"type": "PRIMARY",
                                                         "action": "!DELETE"})

    LOG.info(_LI("Retrieved %(zones)s"), {'zones': domains})

    return flask.jsonify(domains_schema.filter({'domains': domains}))


@blueprint.route('/domains/<uuid:domain_id>', methods=['GET'])
def get_domain(domain_id):
    """Return zone data unless the zone is flagged for purging
    """
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    criterion = {"id": domain_id, "type": "PRIMARY", "action": "!DELETE"}
    domain = central_api.find_zone(context, criterion=criterion)

    LOG.info(_LI("Retrieved %(zone)s"), {'zone': domain})

    return flask.jsonify(domain_schema.filter(domain))


@blueprint.route('/domains/<uuid:domain_id>', methods=['PUT'])
def update_domain(domain_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Fetch the existing resource
    criterion = {"id": domain_id, "type": "PRIMARY", "action": "!DELETE"}
    domain = central_api.find_zone(context, criterion=criterion)

    # Prepare a dict of fields for validation
    domain_data = domain_schema.filter(domain)
    domain_data.update(values)

    # Validate the new set of data
    domain_schema.validate(domain_data)

    # Update and persist the resource
    domain.update(values)
    domain = central_api.update_zone(context, domain)

    LOG.info(_LI("Updated %(zone)s"), {'zone': domain})

    return flask.jsonify(domain_schema.filter(domain))


@blueprint.route('/domains/<uuid:domain_id>', methods=['DELETE'])
def delete_domain(domain_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # TODO(ekarlso): Fix this to something better.
    criterion = {"id": domain_id, "type": "PRIMARY", "action": "!DELETE"}
    central_api.find_zone(context, criterion=criterion)

    domain = central_api.delete_zone(context, domain_id)

    LOG.info(_LI("Deleted %(zone)s"), {'zone': domain})

    return flask.Response(status=200)


@blueprint.route('/domains/<uuid:domain_id>/servers', methods=['GET'])
def get_domain_servers(domain_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # TODO(ekarlso): Fix this to something better.
    criterion = {"id": domain_id, "type": "PRIMARY", "action": "!DELETE"}
    central_api.find_zone(context, criterion=criterion)

    nameservers = central_api.get_zone_ns_records(context, domain_id)

    servers = objects.ServerList()

    for ns in nameservers:
        servers.append(_pool_ns_record_to_server(ns))

    return flask.jsonify(servers_schema.filter({'servers': servers}))
