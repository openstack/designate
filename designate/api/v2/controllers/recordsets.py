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
from oslo_log import log as logging

from designate import exceptions
from designate import schema
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.views import recordsets as recordsets_view
from designate.objects import RecordSet
from designate.objects import Record


LOG = logging.getLogger(__name__)


class RecordSetsController(rest.RestController):
    _view = recordsets_view.RecordSetsView()
    _resource_schema = schema.Schema('v2', 'recordset')
    _collection_schema = schema.Schema('v2', 'recordsets')
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'domain_id', 'tenant_id',
                 'name', 'type', 'ttl', 'records']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def get_one(self, zone_id, recordset_id):
        """Get RecordSet"""
        request = pecan.request
        context = request.environ['context']

        recordset = self.central_api.get_recordset(context, zone_id,
                                                   recordset_id)

        return self._view.show(context, request, recordset)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def get_all(self, zone_id, **params):
        """List RecordSets"""
        request = pecan.request
        context = request.environ['context']

        # NOTE: We need to ensure the domain actually exists, otherwise we may
        #       return deleted recordsets instead of a domain not found
        self.central_api.get_domain(context, zone_id)

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params.
        accepted_filters = ('name', 'type', 'ttl', 'data', )
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        criterion['domain_id'] = zone_id

        # Data must be filtered separately, through the Records table
        recordsets_with_data = set()
        data = criterion.pop('data', None)

        # Retrieve recordsets
        recordsets = self.central_api.find_recordsets(
            context, criterion, marker, limit, sort_key, sort_dir)

        # 'data' filter param: only return recordsets with matching data
        if data:
            records = self.central_api.find_records(
                context, criterion={'data': data, 'domain_id': zone_id})
            recordsets_with_data.update(
                [record.recordset_id for record in records])
            recordsets = [recordset for recordset in recordsets
                          if recordset.id in recordsets_with_data]

        return self._view.list(context, request, recordsets, [zone_id])

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Create RecordSet"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # SOA recordsets cannot be created manually
        if values['type'] == 'SOA':
            raise exceptions.BadRequest(
                "Creating a SOA recordset is now allowed")

        # Create the recordset
        recordset = self.central_api.create_recordset(
            context, zone_id, RecordSet(**values))

        # Prepare the response headers
        if recordset['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201
        response.headers['Location'] = self._view._get_resource_href(
            request, recordset, [zone_id])

        # Prepare and return the response body
        return self._view.show(context, request, recordset)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def put_one(self, zone_id, recordset_id):
        """Update RecordSet"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # Fetch the existing recordset
        recordset = self.central_api.get_recordset(context, zone_id,
                                                   recordset_id)

        # SOA recordsets cannot be updated manually
        if recordset['type'] == 'SOA':
            raise exceptions.BadRequest(
                'Updating SOA recordsets is now allowed')

        # NS recordsets at the zone root cannot be manually updated
        if recordset['type'] == 'NS':
            zone = self.central_api.get_domain(context, zone_id)
            if recordset['name'] == zone['name']:
                raise exceptions.BadRequest(
                    'Updating a root zone NS record is not allowed')

        # Convert to APIv2 Format
        recordset_data = self._view.show(context, request, recordset)
        recordset_data = utils.deep_dict_merge(recordset_data, body)
        new_recordset = self._view.load(context, request, body)

        # Validate the new set of data
        self._resource_schema.validate(recordset_data)

        # Get original list of Records
        original_records = set()
        for record in recordset.records:
            original_records.add(record.data)
        # Get new list of Records
        new_records = set()
        if 'records' in new_recordset:
            for record in new_recordset['records']:
                new_records.add(record.data)
        # Get differences of Records
        records_to_add = new_records.difference(original_records)
        records_to_rm = original_records.difference(new_records)

        # Update all items except records
        record_update = False
        if 'records' in new_recordset:
            record_update = True
            del new_recordset['records']
        recordset.update(new_recordset)

        # Remove deleted records if we have provided a records array
        if record_update:
            recordset.records[:] = [record for record in recordset.records
                                    if record.data not in records_to_rm]

        # Add new records
        for record in records_to_add:
            recordset.records.append(Record(data=record))

        # Persist the resource
        recordset = self.central_api.update_recordset(context, recordset)

        if recordset['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 200

        return self._view.show(context, request, recordset)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def delete_one(self, zone_id, recordset_id):
        """Delete RecordSet"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        # Fetch the existing recordset
        recordset = self.central_api.get_recordset(context, zone_id,
                                                   recordset_id)
        if recordset['type'] == 'SOA':
            raise exceptions.BadRequest(
                'Deleting a SOA recordset is now allowed')

        recordset = self.central_api.delete_recordset(
            context, zone_id, recordset_id)
        response.status_int = 202

        return self._view.show(context, request, recordset)
