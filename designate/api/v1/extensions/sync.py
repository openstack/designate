# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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

from designate.central import rpcapi as central_rpcapi


central_api = central_rpcapi.CentralAPI()
blueprint = flask.Blueprint('sync', __name__)


@blueprint.route('/domains/sync', methods=['POST'])
def sync_domains():
    context = flask.request.environ.get('context')

    central_api.sync_zones(context)

    return flask.Response(status=200)


@blueprint.route('/domains/<uuid:domain_id>/sync', methods=['POST'])
def sync_domain(domain_id):
    context = flask.request.environ.get('context')

    central_api.sync_zone(context, domain_id)

    return flask.Response(status=200)


@blueprint.route('/domains/<uuid:domain_id>/records/<uuid:record_id>/sync',
                 methods=['POST'])
def sync_record(domain_id, record_id):
    context = flask.request.environ.get('context')

    record = central_api.find_record(context, {'id': record_id})
    central_api.sync_record(context, domain_id, record['recordset_id'],
                            record_id)

    return flask.Response(status=200)
