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
from designate import schema
from designate.central import rpcapi as central_rpcapi

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()
blueprint = flask.Blueprint('records', __name__)
record_schema = schema.Schema('v1', 'record')
records_schema = schema.Schema('v1', 'records')


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
    record = central_api.create_record(context, domain_id, values)

    response = flask.jsonify(record_schema.filter(record))
    response.status_int = 201
    response.location = flask.url_for('.get_record', domain_id=domain_id,
                                      record_id=record['id'])

    return response


@blueprint.route('/domains/<uuid:domain_id>/records', methods=['GET'])
def get_records(domain_id):
    context = flask.request.environ.get('context')

    records = central_api.find_records(context, domain_id)

    return flask.jsonify(records_schema.filter({'records': records}))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['GET'])
def get_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    record = central_api.get_record(context, domain_id, record_id)

    return flask.jsonify(record_schema.filter(record))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['PUT'])
def update_record(domain_id, record_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    record = central_api.get_record(context, domain_id, record_id)
    record = record_schema.filter(record)
    record.update(values)

    record_schema.validate(record)
    record = central_api.update_record(context, domain_id, record_id, values)

    return flask.jsonify(record_schema.filter(record))


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>',
                 methods=['DELETE'])
def delete_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    central_api.delete_record(context, domain_id, record_id)

    return flask.Response(status=200)
