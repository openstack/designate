# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

from designate import schema
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.views import tsigkeys as tsigkeys_view
from designate.objects import TsigKey


LOG = logging.getLogger(__name__)


class TsigKeysController(rest.RestController):
    _view = tsigkeys_view.TsigKeysView()
    _resource_schema = schema.Schema('v2', 'tsigkey')
    _collection_schema = schema.Schema('v2', 'tsigkeys')
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'name']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('tsigkey_id')
    def get_one(self, tsigkey_id):
        """Get TsigKey"""

        request = pecan.request
        context = request.environ['context']

        tsigkey = self.central_api.get_tsigkey(context, tsigkey_id)

        return self._view.show(context, request, tsigkey)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List all TsigKeys"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params
        accepted_filters = ('name', 'algorithm', 'scope')
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        tsigkey = self.central_api.find_tsigkeys(
            context, criterion, marker, limit, sort_key, sort_dir)

        return self._view.list(context, request, tsigkey)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create TsigKey"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the tsigkey
        tsigkey = self.central_api.create_tsigkey(
            context, TsigKey(**values))

        response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(
            request, tsigkey)

        # Prepare and return the response body
        return self._view.show(context, request, tsigkey)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('tsigkey_id')
    def patch_one(self, tsigkey_id):
        """Update TsigKey"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # Fetch the existing tsigkey entry
        tsigkey = self.central_api.get_tsigkey(context, tsigkey_id)

        # Convert to APIv2 Format
        tsigkey_data = self._view.show(context, request, tsigkey)

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')
        else:
            tsigkey_data = utils.deep_dict_merge(tsigkey_data, body)

            # Validate the new set of data
            self._resource_schema.validate(tsigkey_data)

            # Update and persist the resource
            tsigkey.update(self._view.load(context, request, body))
            tsigkey = self.central_api.update_tsigkey(context, tsigkey)

        response.status_int = 200

        return self._view.show(context, request, tsigkey)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('tsigkey_id')
    def delete_one(self, tsigkey_id):
        """Delete TsigKey"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.delete_tsigkey(context, tsigkey_id)

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
