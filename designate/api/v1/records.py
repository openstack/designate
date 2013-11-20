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
from designate.openstack.common import log as logging
from designate import exceptions
from designate import schema
from designate.central import rpcapi as central_rpcapi

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()
blueprint = flask.Blueprint('records', __name__)
record_schema = schema.Schema('v1', 'record')
records_schema = schema.Schema('v1', 'records')


def _find_recordset(context, domain_id, name, type):
    return central_api.find_recordset(context, {
        'domain_id': domain_id,
        'name': name,
        'type': type,
    })


def _find_or_create_recordset(context, domain_id, name, type, ttl):
    try:
        recordset = _find_recordset(context, domain_id, name, type)
    except exceptions.RecordSetNotFound:
        recordset = central_api.create_recordset(context, domain_id, {
            'name': name,
            'type': type,
            'ttl': ttl,
        })

    return recordset


def _extract_record_values(values):
    record_values = ('data', 'priority', 'comment',)
    return dict((k, values[k]) for k in record_values if k in values)


def _extract_recordset_values(values):
    recordset_values = ('name', 'type', 'ttl',)
    return dict((k, values[k]) for k in recordset_values if k in values)


def _format_record_v1(record, recordset):
    record.update({
        'name': recordset['name'],
        'type': recordset['type'],
        'ttl': recordset['ttl'],
    })

    return record


def _fetch_domain_recordsets(context, domain_id):
    criterion = {'domain_id': domain_id}

    recordsets = central_api.find_recordsets(context, criterion)

    return dict((r['id'], r) for r in recordsets)


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

    recordset = _find_or_create_recordset(context,
                                          domain_id,
                                          values['name'],
                                          values['type'],
                                          values.get('ttl', None))

    record = central_api.create_record(context, domain_id, recordset['id'],
                                       _extract_record_values(values))

    record = _format_record_v1(record, recordset)

    response = flask.jsonify(record_schema.filter(record))
    response.status_int = 201
    response.location = flask.url_for('.get_record', domain_id=domain_id,
                                      record_id=record['id'])

    return response


@blueprint.route('/domains/<uuid:domain_id>/records', methods=['GET'])
def get_records(domain_id):
    context = flask.request.environ.get('context')

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return an empty records array instead of a domain not found
    central_api.get_domain(context, domain_id)

    records = central_api.find_records(context, {'domain_id': domain_id})

    recordsets = _fetch_domain_recordsets(context, domain_id)

    def _inner(record):
        recordset = recordsets[record['recordset_id']]
        return _format_record_v1(record, recordset)

    records = [_inner(r) for r in records]

    return flask.jsonify(records_schema.filter({'records': records}))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['GET'])
def get_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return an record not found instead of a domain not found
    central_api.get_domain(context, domain_id)

    criterion = {'domain_id': domain_id, 'id': record_id}
    record = central_api.find_record(context, criterion)

    recordset = central_api.get_recordset(
        context, domain_id, record['recordset_id'])

    record = _format_record_v1(record, recordset)

    return flask.jsonify(record_schema.filter(record))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['PUT'])
def update_record(domain_id, record_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return an record not found instead of a domain not found
    central_api.get_domain(context, domain_id)

    # Find the record
    criterion = {'domain_id': domain_id, 'id': record_id}
    record = central_api.find_record(context, criterion)

    # Find the associated recordset
    recordset = central_api.get_recordset(
        context, domain_id, record['recordset_id'])

    # Filter out any extra fields from the fetched record
    record = record_schema.filter(record)

    # Ensure all the API V1 fields are in place
    record = _format_record_v1(record, recordset)

    # Name and Type can't be updated on existing records
    if 'name' in values and record['name'] != values['name']:
        raise exceptions.InvalidOperation('The name field is immutable')

    if 'type' in values and record['type'] != values['type']:
        raise exceptions.InvalidOperation('The type field is immutable')

    # TTL Updates should be applied to the RecordSet
    update_recordset = False

    if 'ttl' in values and record['ttl'] != values['ttl']:
        update_recordset = True

    # Apply the updated fields to the record
    record.update(values)

    # Validate the record
    record_schema.validate(record)

    # Update the record
    record = central_api.update_record(
        context, domain_id, recordset['id'], record_id,
        _extract_record_values(values))

    # Update the recordset (if necessary)
    if update_recordset:
        recordset = central_api.update_recordset(
            context, domain_id, recordset['id'],
            _extract_recordset_values(values))

    # Format and return the response
    record = _format_record_v1(record, recordset)

    return flask.jsonify(record_schema.filter(record))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['DELETE'])
def delete_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    # NOTE: We need to ensure the domain actually exists, otherwise we may
    #       return a record not found instead of a domain not found
    central_api.get_domain(context, domain_id)

    # Find the record
    criterion = {'domain_id': domain_id, 'id': record_id}
    record = central_api.find_record(context, criterion)

    central_api.delete_record(
        context, domain_id, record['recordset_id'], record_id)

    return flask.Response(status=200)
