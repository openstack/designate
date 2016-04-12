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

from designate.central import rpcapi as central_rpcapi
from designate import exceptions
from designate import objects
from designate import schema
from designate import utils
from designate.i18n import _LI


LOG = logging.getLogger(__name__)
blueprint = flask.Blueprint('records', __name__)
record_schema = schema.Schema('v1', 'record')
records_schema = schema.Schema('v1', 'records')


def _find_recordset(context, domain_id, name, type):
    central_api = central_rpcapi.CentralAPI.get_instance()

    return central_api.find_recordset(context, {
        'zone_id': domain_id,
        'name': name,
        'type': type,
    })


def _find_or_create_recordset(context, domain_id, name, type, ttl):
    central_api = central_rpcapi.CentralAPI.get_instance()

    criterion = {"id": domain_id, "type": "PRIMARY", "action": "!DELETE"}
    central_api.find_zone(context, criterion=criterion)

    try:
        # Attempt to create an empty recordset
        values = {
            'name': name,
            'type': type,
            'ttl': ttl,
        }

        recordset = central_api.create_recordset(
            context, domain_id, objects.RecordSet(**values))

    except exceptions.DuplicateRecordSet:
        # Fetch the existing recordset
        recordset = _find_recordset(context, domain_id, name, type)

    return recordset


def _extract_record_values(values):
    record_values = dict((k, values[k]) for k in ('data', 'description',)
                         if k in values)
    if values.get('priority', None) is not None:
        record_values['data'] = '%d %s' % (
            values['priority'], record_values['data'])
    return record_values


def _extract_recordset_values(values):
    recordset_values = ('name', 'type', 'ttl',)
    return dict((k, values[k]) for k in recordset_values if k in values)


def _format_record_v1(record, recordset):
    record = dict(record)

    record['priority'], record['data'] = utils.extract_priority_from_data(
        recordset.type, record)

    record['domain_id'] = record['zone_id']

    del record['zone_id']

    record.update({
        'name': recordset['name'],
        'type': recordset['type'],
        'ttl': recordset['ttl'],
    })

    return record


@blueprint.route('/schemas/record', methods=['GET'])
def get_record_schema():
    return flask.jsonify(record_schema.raw)


@blueprint.route('/schemas/records', methods=['GET'])
def get_records_schema():
    return flask.jsonify(records_schema.raw)


@blueprint.route('/domains/<uuid:domain_id>/records', methods=['POST'])
def create_record(domain_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    record_schema.validate(values)

    if values['type'] == 'SOA':
        raise exceptions.BadRequest('SOA records cannot be manually created.')

    recordset = _find_or_create_recordset(context,
                                          domain_id,
                                          values['name'],
                                          values['type'],
                                          values.get('ttl', None))

    record = objects.Record(**_extract_record_values(values))

    central_api = central_rpcapi.CentralAPI.get_instance()
    record = central_api.create_record(context, domain_id,
                                       recordset['id'],
                                       record)
    LOG.info(_LI("Created %(record)s"), {'record': record})

    record = _format_record_v1(record, recordset)

    response = flask.jsonify(record_schema.filter(record))
    response.status_int = 201
    response.location = flask.url_for('.get_record', domain_id=domain_id,
                                      record_id=record['id'])

    return response


@blueprint.route('/domains/<uuid:domain_id>/records', methods=['GET'])
def get_records(domain_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return an empty records array instead of a domain not found
    central_api.get_zone(context, domain_id)

    recordsets = central_api.find_recordsets(context, {'zone_id': domain_id})
    LOG.info(_LI("Retrieved %(recordsets)s"), {'recordsets': recordsets})

    records = []

    for rrset in recordsets:
        records.extend([_format_record_v1(r, rrset) for r in rrset.records])

    return flask.jsonify(records_schema.filter({'records': records}))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['GET'])
def get_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return an record not found instead of a domain not found
    central_api.get_zone(context, domain_id)

    criterion = {'zone_id': domain_id, 'id': record_id}
    record = central_api.find_record(context, criterion)

    recordset = central_api.get_recordset(
        context, domain_id, record['recordset_id'])

    LOG.info(_LI("Retrieved %(recordset)s"), {'recordset': recordset})

    record = _format_record_v1(record, recordset)

    return flask.jsonify(record_schema.filter(record))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['PUT'])
def update_record(domain_id, record_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    central_api = central_rpcapi.CentralAPI.get_instance()

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return a record not found instead of a domain not found
    criterion = {"id": domain_id, "type": "PRIMARY", "action": "!DELETE"}
    central_api.find_zone(context, criterion)

    # Fetch the existing resource
    # NOTE(kiall): We use "find_record" rather than "get_record" as we do not
    #              have the recordset_id.
    criterion = {'zone_id': domain_id, 'id': record_id}
    record = central_api.find_record(context, criterion)

    # TODO(graham): Move this further down the stack
    if record.managed and not context.edit_managed_records:
        raise exceptions.BadRequest('Managed records may not be updated')

    # Find the associated recordset
    recordset = central_api.get_recordset(
        context, domain_id, record.recordset_id)

    # Prepare a dict of fields for validation
    record_data = record_schema.filter(_format_record_v1(record, recordset))
    record_data.update(values)

    # Validate the new set of data
    record_schema.validate(record_data)

    # Update and persist the resource
    record.update(_extract_record_values(values))
    record = central_api.update_record(context, record)

    # Update the recordset resource (if necessary)
    recordset.update(_extract_recordset_values(values))
    if len(recordset.obj_what_changed()) > 0:
        recordset = central_api.update_recordset(context, recordset)
        LOG.info(_LI("Updated %(recordset)s"), {'recordset': recordset})

    # Format and return the response
    record = _format_record_v1(record, recordset)

    return flask.jsonify(record_schema.filter(record))


def _delete_recordset_if_empty(context, domain_id, recordset_id):
    central_api = central_rpcapi.CentralAPI.get_instance()

    recordset = central_api.find_recordset(context, {
        'id': recordset_id
    })
    # Make sure it's the right recordset
    if len(recordset.records) == 0:
        recordset = central_api.delete_recordset(
            context, domain_id, recordset_id)
        LOG.info(_LI("Deleted %(recordset)s"), {'recordset': recordset})


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['DELETE'])
def delete_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return a record not found instead of a domain not found
    criterion = {"id": domain_id, "type": "PRIMARY", "action": "!DELETE"}
    central_api.find_zone(context, criterion=criterion)

    # Find the record
    criterion = {'zone_id': domain_id, 'id': record_id}
    record = central_api.find_record(context, criterion)

    # Cannot delete a managed record via the API.
    if record['managed'] is True:
        raise exceptions.BadRequest('Managed records may not be deleted')

    record = central_api.delete_record(
        context, domain_id, record['recordset_id'], record_id)
    LOG.info(_LI("Deleted %(record)s"), {'record': record})

    _delete_recordset_if_empty(context, domain_id, record['recordset_id'])
    return flask.Response(status=200)
