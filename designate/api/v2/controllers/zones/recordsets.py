# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from oslo_log import log as logging
import pecan

from designate.api.v2.controllers import common
from designate.api.v2.controllers import rest
from designate import exceptions
from designate.objects.adapters import DesignateAdapter
from designate.objects import RecordSet
from designate import utils

LOG = logging.getLogger(__name__)


class RecordSetsController(rest.RestController):
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'zone_id', 'tenant_id',
                 'name', 'type', 'ttl', 'records']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id', 'recordset_id')
    def get_one(self, zone_id, recordset_id):
        """Get RecordSet"""
        request = pecan.request
        context = request.environ['context']

        return DesignateAdapter.render('API_v2',
                                       self.central_api.get_recordset(
                                           context, zone_id, recordset_id),
                                       request=request)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def get_all(self, zone_id, **params):
        """List RecordSets"""
        request = pecan.request
        context = request.environ['context']
        recordsets = common.retrieve_matched_rrsets(context, self, zone_id,
                                                    **params)

        return DesignateAdapter.render('API_v2', recordsets, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Create RecordSet"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        body = request.body_dict

        recordset = DesignateAdapter.parse('API_v2', body, RecordSet())

        recordset.validate()

        # SOA recordsets cannot be created manually
        if recordset.type == 'SOA':
            raise exceptions.BadRequest(
                'Creating a SOA recordset is not allowed'
            )

        # Create the recordset
        recordset = self.central_api.create_recordset(
            context, zone_id, recordset)

        # Prepare the response headers
        if recordset['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201

        recordset = DesignateAdapter.render('API_v2', recordset,
                                            request=request)

        response.headers['Location'] = recordset['links']['self']

        # Prepare and return the response body
        return recordset

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
        # TODO(graham): Move this further down the stack
        if recordset.managed and not context.edit_managed_records:
            raise exceptions.BadRequest('Managed records may not be updated')

        # SOA recordsets cannot be updated manually
        if recordset['type'] == 'SOA':
            raise exceptions.BadRequest(
                'Updating SOA recordsets is not allowed'
            )

        # NS recordsets at the zone root cannot be manually updated
        if recordset['type'] == 'NS':
            zone = self.central_api.get_zone(context, zone_id)
            if recordset['name'] == zone['name']:
                raise exceptions.BadRequest(
                    'Updating a root zone NS record is not allowed'
                )

        # Convert to APIv2 Format

        recordset = DesignateAdapter.parse('API_v2', body, recordset)

        recordset.validate()

        # Persist the resource
        recordset = self.central_api.update_recordset(context, recordset)

        if recordset['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 200

        return DesignateAdapter.render('API_v2', recordset, request=request)

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
                'Deleting a SOA recordset is not allowed')

        recordset = self.central_api.delete_recordset(
            context, zone_id, recordset_id)
        response.status_int = 202

        return DesignateAdapter.render('API_v2', recordset, request=request)
