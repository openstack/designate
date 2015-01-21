# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import pecan
from oslo_log import log as logging

from designate import schema
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.views import tlds as tlds_view
from designate.objects import Tld


LOG = logging.getLogger(__name__)


class TldsController(rest.RestController):
    _view = tlds_view.TldsView()
    _resource_schema = schema.Schema('v2', 'tld')
    _collection_schema = schema.Schema('v2', 'tlds')
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'name']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('tld_id')
    def get_one(self, tld_id):
        """Get Tld"""

        request = pecan.request
        context = request.environ['context']

        tld = self.central_api.get_tld(context, tld_id)
        return self._view.show(context, request, tld)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Tlds"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params.
        accepted_filters = ('name')
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        tlds = self.central_api.find_tlds(
            context, criterion, marker, limit, sort_key, sort_dir)

        return self._view.list(context, request, tlds)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create Tld"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the tld
        tld = self.central_api.create_tld(context, Tld(**values))
        response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(request,
                                                                     tld)
        # Prepare and return the response body
        return self._view.show(context, request, tld)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('tld_id')
    def patch_one(self, tld_id):
        """Update Tld"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # Fetch the existing tld
        tld = self.central_api.get_tld(context, tld_id)

        # Convert to APIv2 Format
        tld_data = self._view.show(context, request, tld)

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')
        else:
            tld_data = utils.deep_dict_merge(tld_data, body)

            # Validate the new set of data
            self._resource_schema.validate(tld_data)

            # Update and persist the resource
            tld.update(self._view.load(context, request, body))
            tld = self.central_api.update_tld(context, tld)

        response.status_int = 200

        return self._view.show(context, request, tld)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('tld_id')
    def delete_one(self, tld_id):
        """Delete Tld"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.delete_tld(context, tld_id)

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
