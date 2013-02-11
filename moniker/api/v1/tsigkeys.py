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
blueprint = flask.Blueprint('tsigkeys', __name__)
tsigkey_schema = schema.Schema('v1', 'tsigkey')
tsigkeys_schema = schema.Schema('v1', 'tsigkeys')


@blueprint.route('/schemas/tsigkey', methods=['GET'])
def get_tsigkey_schema():
    return flask.jsonify(tsigkey_schema.raw)


@blueprint.route('/schemas/tsigkeys', methods=['GET'])
def get_tsigkeys_schema():
    return flask.jsonify(tsigkeys_schema.raw)


@blueprint.route('/tsigkeys', methods=['POST'])
def create_tsigkey():
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        tsigkey_schema.validate(values)
        tsigkey = central_api.create_tsigkey(context,
                                             values=flask.request.json)
    except exceptions.InvalidObject, e:
        response_body = json.dumps({'errors': e.errors})
        return flask.Response(status=400, response=response_body)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.DuplicateTsigKey:
        return flask.Response(status=409)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        tsigkey = tsigkey_schema.filter(tsigkey)

        response = flask.jsonify(tsigkey)
        response.status_int = 201
        response.location = flask.url_for('.get_tsigkey',
                                          tsigkey_id=tsigkey['id'])
        return response


@blueprint.route('/tsigkeys', methods=['GET'])
def get_tsigkeys():
    context = flask.request.environ.get('context')

    try:
        tsigkeys = central_api.get_tsigkeys(context)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except rpc_common.Timeout:
        return flask.Response(status=504)

    tsigkeys = tsigkeys_schema.filter({'tsigkeys': tsigkeys})

    return flask.jsonify(tsigkeys)


@blueprint.route('/tsigkeys/<tsigkey_id>', methods=['GET'])
def get_tsigkey(tsigkey_id):
    context = flask.request.environ.get('context')

    try:
        tsigkey = central_api.get_tsigkey(context, tsigkey_id)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.TsigKeyNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        tsigkey = tsigkey_schema.filter(tsigkey)

        return flask.jsonify(tsigkey)


@blueprint.route('/tsigkeys/<tsigkey_id>', methods=['PUT'])
def update_tsigkey(tsigkey_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    try:
        tsigkey = central_api.get_tsigkey(context, tsigkey_id)
        tsigkey.update(values)

        tsigkey_schema.validate(tsigkey)
        tsigkey = central_api.update_tsigkey(context, tsigkey_id,
                                             values=values)
    except exceptions.InvalidObject, e:
        response_body = json.dumps({'errors': e.errors})
        return flask.Response(status=400, response=response_body)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.TsigKeyNotFound:
        return flask.Response(status=404)
    except exceptions.DuplicateTsigKey:
        return flask.Response(status=409)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        tsigkey = tsigkey_schema.filter(tsigkey)

        return flask.jsonify(tsigkey)


@blueprint.route('/tsigkeys/<tsigkey_id>', methods=['DELETE'])
def delete_tsigkey(tsigkey_id):
    context = flask.request.environ.get('context')

    try:
        central_api.delete_tsigkey(context, tsigkey_id)
    except exceptions.BadRequest:
        return flask.Response(status=400)
    except exceptions.Forbidden:
        return flask.Response(status=401)
    except exceptions.TsigKeyNotFound:
        return flask.Response(status=404)
    except rpc_common.Timeout:
        return flask.Response(status=504)
    else:
        return flask.Response(status=200)
