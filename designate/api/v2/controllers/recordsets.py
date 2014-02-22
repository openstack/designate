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
from designate.api.v2.views import recordsets as recordsets_view
from designate.api.v2.controllers import records

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()


class RecordSetsController(rest.RestController):
    _view = recordsets_view.RecordSetsView()
    _resource_schema = schema.Schema('v2', 'recordset')
    _collection_schema = schema.Schema('v2', 'recordsets')
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'domain_id', 'tenant_id',
                 'name', 'type', 'ttl']

    records = records.RecordsController()

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def get_one(self, zone_id, recordset_id):
        """ Get RecordSet """
        request = pecan.request
        context = request.environ['context']

        recordset = central_api.get_recordset(context, zone_id, recordset_id)

        return self._view.show(context, request, recordset)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def get_all(self, zone_id, **params):
        """ List RecordSets """
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params.
        accepted_filters = ('name', 'type', 'ttl', )
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        criterion['domain_id'] = zone_id

        recordsets = central_api.find_recordsets(
            context, criterion, marker, limit, sort_key, sort_dir)

        return self._view.list(context, request, recordsets, [zone_id])

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """ Create RecordSet """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the recordset
        recordset = central_api.create_recordset(context, zone_id, values)

        # Prepare the response headers
        response.status_int = 201
        response.headers['Location'] = self._view._get_resource_href(
            request, recordset, [zone_id])

        # Prepare and return the response body
        return self._view.show(context, request, recordset)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def patch_one(self, zone_id, recordset_id):
        """ Update RecordSet """
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # Fetch the existing recordset
        recordset = central_api.get_recordset(context, zone_id, recordset_id)

        # Convert to APIv2 Format
        recordset = self._view.show(context, request, recordset)

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')
        else:
            recordset = utils.deep_dict_merge(recordset, body)

            # Validate the request conforms to the schema
            self._resource_schema.validate(recordset)

            values = self._view.load(context, request, body)
            recordset = central_api.update_recordset(
                context, zone_id, recordset_id, values)

        response.status_int = 200

        return self._view.show(context, request, recordset)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def delete_one(self, zone_id, recordset_id):
        """ Delete RecordSet """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        central_api.delete_recordset(context, zone_id, recordset_id)

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
