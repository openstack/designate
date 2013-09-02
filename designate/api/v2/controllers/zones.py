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
from designate import utils
from designate import schema
from designate.api.v2.controllers import rest
from designate.api.v2.controllers import recordsets
from designate.api.v2.views import zones as zones_view
from designate.central import rpcapi as central_rpcapi
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()


class ZonesController(rest.RestController):
    _view = zones_view.ZonesView()
    _resource_schema = schema.Schema('v2', 'zone')
    _collection_schema = schema.Schema('v2', 'zones')

    recordsets = recordsets.RecordSetsController()

    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, zone_id):
        """ Get Zone """
        request = pecan.request
        context = request.environ['context']

        # TODO(kiall): Validate we have a sane UUID for zone_id

        zone = central_api.get_domain(context, zone_id)

        return self._view.detail(context, request, zone)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """ List Zones """
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        #marker = params.pop('marker', None)
        #limit = int(params.pop('limit', 30))

        # Extract any filter params.
        accepted_filters = ('name', 'email')
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        zones = central_api.find_domains(context, criterion)

        return self._view.list(context, request, zones)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """ Create Zone """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the zone
        zone = central_api.create_domain(context, values)

        # Prepare the response headers
        # If the zone has been created asynchronously

        if zone['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(request,
                                                                     zone)

        # Prepare and return the response body
        return self._view.detail(context, request, zone)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    def patch_one(self, zone_id):
        """ Update Zone """
        # TODO(kiall): This needs cleanup to say the least..
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # TODO(kiall): Validate we have a sane UUID for zone_id

        # Fetch the existing zone
        zone = central_api.get_domain(context, zone_id)

        # Convert to APIv2 Format
        zone = self._view.detail(context, request, zone)

        if request.content_type == 'application/json-patch+json':
            # Possible pattern:
            #
            # 1) Load existing zone.
            # 2) Apply patch, maintain list of changes.
            # 3) Return changes, after passing through the code ^ for plain
            #    JSON.
            #
            # Difficulties:
            #
            # 1) "Nested" resources? records inside a recordset.
            # 2) What to do when a zone doesn't exist in the first place?
            # 3) ...?
            raise NotImplemented('json-patch not implemented')
        else:
            zone = utils.deep_dict_merge(zone, body)

            # Validate the request conforms to the schema
            self._resource_schema.validate(zone)

            values = self._view.load(context, request, body)
            zone = central_api.update_domain(context, zone_id, values)

        if zone['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 200

        return self._view.detail(context, request, zone)

    @pecan.expose(template=None, content_type='application/json')
    def delete_one(self, zone_id):
        """ Delete Zone """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        # TODO(kiall): Validate we have a sane UUID for zone_id

        zone = central_api.delete_domain(context, zone_id)

        if zone['status'] == 'DELETING':
            response.status_int = 202
        else:
            response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
