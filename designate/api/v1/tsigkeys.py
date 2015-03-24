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
from oslo_config import cfg

from designate import schema
from designate.central import rpcapi as central_rpcapi
from designate.objects import TsigKey
from designate.i18n import _LI


LOG = logging.getLogger(__name__)
blueprint = flask.Blueprint('tsigkeys', __name__)
tsigkey_schema = schema.Schema('v1', 'tsigkey')
tsigkeys_schema = schema.Schema('v1', 'tsigkeys')
default_pool_id = cfg.CONF['service:central'].default_pool_id


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

    central_api = central_rpcapi.CentralAPI.get_instance()

    tsigkey_schema.validate(values)

    tsigkey = TsigKey.from_dict(values)

    # The V1 API only deals with the default pool, so we restrict the view
    # of TSIG Keys to those scoped to the default pool.
    tsigkey.scope = 'POOL'
    tsigkey.resource_id = default_pool_id

    tsigkey = central_api.create_tsigkey(context, tsigkey)

    LOG.info(_LI("Created %(tsigkey)s"), {'tsigkey': tsigkey})

    response = flask.jsonify(tsigkey_schema.filter(tsigkey))
    response.status_int = 201
    response.location = flask.url_for('.get_tsigkey', tsigkey_id=tsigkey['id'])

    return response


@blueprint.route('/tsigkeys', methods=['GET'])
def get_tsigkeys():
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    criterion = {'scope': 'POOL', 'resource_id': default_pool_id}
    tsigkeys = central_api.find_tsigkeys(context, criterion)

    LOG.info(_LI("Retrieved %(tsigkeys)s"), {'tsigkeys': tsigkeys})

    return flask.jsonify(tsigkeys_schema.filter({'tsigkeys': tsigkeys}))


@blueprint.route('/tsigkeys/<uuid:tsigkey_id>', methods=['GET'])
def get_tsigkey(tsigkey_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    criterion = {
        'scope': 'POOL',
        'resource_id': default_pool_id,
        'id': tsigkey_id,
    }

    tsigkey = central_api.find_tsigkeys(context, criterion)

    LOG.info(_LI("Retrieved %(tsigkey)s"), {'tsigkey': tsigkey})

    return flask.jsonify(tsigkey_schema.filter(tsigkey))


@blueprint.route('/tsigkeys/<uuid:tsigkey_id>', methods=['PUT'])
def update_tsigkey(tsigkey_id):
    context = flask.request.environ.get('context')
    values = flask.request.json

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Fetch the existing tsigkey
    criterion = {
        'scope': 'POOL',
        'resource_id': default_pool_id,
        'id': tsigkey_id,
    }

    tsigkey = central_api.find_tsigkey(context, criterion)

    # Prepare a dict of fields for validation
    tsigkey_data = tsigkey_schema.filter(tsigkey)
    tsigkey_data.update(values)

    # Validate the new set of data
    tsigkey_schema.validate(tsigkey_data)

    # Update and persist the resource
    tsigkey.update(values)
    tsigkey = central_api.update_tsigkey(context, tsigkey)

    LOG.info(_LI("Updated %(tsigkey)s"), {'tsigkey': tsigkey})

    return flask.jsonify(tsigkey_schema.filter(tsigkey))


@blueprint.route('/tsigkeys/<uuid:tsigkey_id>', methods=['DELETE'])
def delete_tsigkey(tsigkey_id):
    context = flask.request.environ.get('context')

    central_api = central_rpcapi.CentralAPI.get_instance()

    # Fetch the existing resource, this ensures the key to be deleted has the
    # correct scope/resource_id values, otherwise it will trigger a 404.
    criterion = {
        'scope': 'POOL',
        'resource_id': default_pool_id,
        'id': tsigkey_id,
    }
    central_api.find_tsigkeys(context, criterion)

    # Delete the TSIG Key
    tsigkey = central_api.delete_tsigkey(context, tsigkey_id)

    LOG.info(_LI("Deleted %(tsigkey)s"), {'tsigkey': tsigkey})

    return flask.Response(status=200)
