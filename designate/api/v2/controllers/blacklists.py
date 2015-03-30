# Copyright 2014 Rackspace
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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
from designate.objects import Blacklist
from designate.objects.adapters import DesignateAdapter


LOG = logging.getLogger(__name__)


class BlacklistsController(rest.RestController):
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'pattern']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('blacklist_id')
    def get_one(self, blacklist_id):
        """Get Blacklist"""

        request = pecan.request
        context = request.environ['context']

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.get_blacklist(context, blacklist_id),
            request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List all Blacklisted Zones"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params
        accepted_filters = ('pattern')
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.find_blacklists(
                context, criterion, marker, limit, sort_key, sort_dir),
            request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create Blacklisted Zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        blacklist = DesignateAdapter.parse('API_v2', body, Blacklist())

        blacklist.validate()

        # Create the blacklist
        blacklist = self.central_api.create_blacklist(
            context, blacklist)

        response.status_int = 201

        blacklist = DesignateAdapter.render(
            'API_v2', blacklist, request=request)

        response.headers['Location'] = blacklist['links']['self']

        # Prepare and return the response body
        return blacklist

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('blacklist_id')
    def patch_one(self, blacklist_id):
        """Update Blacklisted Zone"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')

        # Fetch the existing blacklist entry
        blacklist = self.central_api.get_blacklist(context, blacklist_id)

        blacklist = DesignateAdapter.parse('API_v2', body, blacklist)

        blacklist.validate()

        blacklist = self.central_api.update_blacklist(context, blacklist)

        response.status_int = 200

        return DesignateAdapter.render('API_v2', blacklist, request=request)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('blacklist_id')
    def delete_one(self, blacklist_id):
        """Delete Blacklisted Zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.delete_blacklist(context, blacklist_id)

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
