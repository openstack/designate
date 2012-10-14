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
from moniker import exceptions
from moniker.api.v1 import blueprint
from moniker.api.v1.schemas import record_schema, records_schema
from moniker.central import api as central_api

LOG = logging.getLogger(__name__)


def _append_record_links(values, domain_id, record_id):
    values['self'] = flask.url_for('.get_record', domain_id=domain_id,
                                   record_id=record_id)
    values['domain'] = flask.url_for('.get_domain', domain_id=domain_id)
    values['schema'] = flask.url_for('.get_record_schema')

    return values


@blueprint.route('/schemas/record', methods=['GET'])
def get_record_schema():
    return flask.jsonify(record_schema.raw())


@blueprint.route('/schemas/records', methods=['GET'])
def get_records_schema():
    return flask.jsonify(records_schema.raw())


@blueprint.route('/domains/<domain_id>/records', methods=['POST'])
def create_record(domain_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        record_schema.validate(values)
        record = central_api.create_record(context, domain_id, values)
    except exceptions.InvalidObject, e:
        return flask.Response(status=400, response=str(e))
    except exceptions.DuplicateRecord:
        return flask.Response(status=409)
    else:
        record = _append_record_links(record, record['domain_id'],
                                      record['id'])
        record = record_schema.filter(record)

        response = flask.jsonify(record)
        response.status_int = 201
        response.location = flask.url_for('.get_record',
                                          domain_id=domain_id,
                                          record_id=record['id'])
        return response


@blueprint.route('/domains/<domain_id>/records', methods=['GET'])
def get_records(domain_id):
    context = flask.request.environ.get('context')

    records = central_api.get_records(context, domain_id)

    return flask.jsonify(records=records)


@blueprint.route('/domains/<domain_id>/records/<record_id>', methods=['GET'])
def get_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    try:
        record = central_api.get_record(context, domain_id, record_id)
    except exceptions.RecordNotFound:
        return flask.Response(status=404)
    else:
        record = _append_record_links(record, record['domain_id'],
                                      record['id'])
        record = record_schema.filter(record)

        return flask.jsonify(record)


@blueprint.route('/domains/<domain_id>/records/<record_id>', methods=['PUT'])
def update_record(domain_id, record_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        record_schema.validate(values)
        record = central_api.update_record(context, domain_id, record_id,
                                           values)
    except exceptions.InvalidObject, e:
        return flask.Response(status=400, response=str(e))
    except exceptions.RecordNotFound:
        return flask.Response(status=404)
    except exceptions.DuplicateRecord:
        return flask.Response(status=409)
    else:
        record = _append_record_links(record, record['domain_id'],
                                      record['id'])
        record = record_schema.filter(record)

        return flask.jsonify(record)


@blueprint.route('/domains/<domain_id>/records/<record_id>',
                 methods=['DELETE'])
def delete_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    try:
        central_api.delete_record(context, domain_id, record_id)
    except exceptions.RecordNotFound:
        return flask.Response(status=404)
    else:
        return flask.Response(status=200)
