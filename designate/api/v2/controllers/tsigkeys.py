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

from designate import utils
from designate.api.v2.controllers import rest
from designate.objects import TsigKey
from designate.objects.adapters import DesignateAdapter

LOG = logging.getLogger(__name__)


class TsigKeysController(rest.RestController):
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'name']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('tsigkey_id')
    def get_one(self, tsigkey_id):
        """Get TsigKey"""

        request = pecan.request
        context = request.environ['context']

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.get_tsigkey(context, tsigkey_id),
            request=request)

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

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.find_tsigkeys(
                context, criterion, marker, limit, sort_key, sort_dir),
            request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create TsigKey"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        tsigkey = DesignateAdapter.parse('API_v2', body, TsigKey())

        tsigkey.validate()

        # Create the tsigkey
        tsigkey = self.central_api.create_tsigkey(
            context, tsigkey)

        tsigkey = DesignateAdapter.render('API_v2', tsigkey, request=request)

        response.headers['Location'] = tsigkey['links']['self']
        response.status_int = 201
        # Prepare and return the response body
        return tsigkey

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('tsigkey_id')
    def patch_one(self, tsigkey_id):
        """Update TsigKey"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')

        # Fetch the existing tsigkey entry
        tsigkey = self.central_api.get_tsigkey(context, tsigkey_id)

        tsigkey = DesignateAdapter.parse('API_v2', body, tsigkey)

        # Validate the new set of data
        tsigkey.validate()

        # Update and persist the resource
        tsigkey = self.central_api.update_tsigkey(context, tsigkey)

        response.status_int = 200

        return DesignateAdapter.render('API_v2', tsigkey, request=request)

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
