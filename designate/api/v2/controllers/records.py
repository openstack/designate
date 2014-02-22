# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import pecan
from designate.central import rpcapi as central_rpcapi
from designate.openstack.common import log as logging
from designate import schema
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.views import records as records_view

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()


class RecordsController(rest.RestController):
    _view = records_view.RecordsView()
    _resource_schema = schema.Schema('v2', 'record')
    _collection_schema = schema.Schema('v2', 'records')
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'domain_id', 'tenant_id',
                 'recordset_id', 'status']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id', 'record_id')
    def get_one(self, zone_id, recordset_id, record_id):
        """ Get Record """
        request = pecan.request
        context = request.environ['context']

        record = central_api.get_record(context, zone_id, recordset_id,
                                        record_id)

        return self._view.show(context, request, record)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def get_all(self, zone_id, recordset_id, **params):
        """ List Records """
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params.
        accepted_filters = ('data', )
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        criterion['domain_id'] = zone_id
        criterion['recordset_id'] = recordset_id

        records = central_api.find_records(
            context, criterion, marker, limit, sort_key, sort_dir)

        return self._view.list(context, request, records,
                               [zone_id, recordset_id])

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def post_all(self, zone_id, recordset_id):
        """ Create Record """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the records
        record = central_api.create_record(context, zone_id, recordset_id,
                                           values)

        # Prepare the response headers
        if record['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(
            request, record, [zone_id, recordset_id])

        # Prepare and return the response body
        return self._view.show(context, request, record)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('zone_id', 'recordset_id', 'record_id')
    def patch_one(self, zone_id, recordset_id, record_id):
        """ Update Record """
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # Fetch the existing record
        record = central_api.get_record(context, zone_id, recordset_id,
                                        record_id)

        # Convert to APIv2 Format
        record = self._view.show(context, request, record)

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')
        else:
            record = utils.deep_dict_merge(record, body)

            # Validate the request conforms to the schema
            self._resource_schema.validate(record)

            values = self._view.load(context, request, body)
            record = central_api.update_record(
                context, zone_id, recordset_id, record_id, values)

        if record['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 200

        return self._view.show(context, request, record)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id', 'record_id')
    def delete_one(self, zone_id, recordset_id, record_id):
        """ Delete Record """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        record = central_api.delete_record(context, zone_id, recordset_id,
                                           record_id)

        if record['status'] == 'DELETING':
            response.status_int = 202
        else:
            response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
