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
from designate.central import rpcapi as central_rpcapi
from designate.openstack.common import log as logging
from designate import schema
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.views import blacklists as blacklists_view

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()


class BlacklistsController(rest.RestController):
    _view = blacklists_view.BlacklistsView()
    _resource_schema = schema.Schema('v2', 'blacklist')
    _collection_schema = schema.Schema('v2', 'blacklists')
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'pattern']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('blacklist_id')
    def get_one(self, blacklist_id):
        """ Get Blacklist """

        request = pecan.request
        context = request.environ['context']

        blacklist = central_api.get_blacklist(context, blacklist_id)

        return self._view.show(context, request, blacklist)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """ List all Blacklisted Zones """
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params
        accepted_filters = ('pattern')
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        blacklist = central_api.find_blacklists(
            context, criterion, marker, limit, sort_key, sort_dir)

        return self._view.list(context, request, blacklist)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """ Create Blacklisted Zone """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the blacklist
        blacklist = central_api.create_blacklist(context, values)

        response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(
            request, blacklist)

        # Prepare and return the response body
        return self._view.show(context, request, blacklist)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('blacklist_id')
    def patch_one(self, blacklist_id):
        """ Update Blacklisted Zone """
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # Fetch the existing blacklisted zone
        blacklist = central_api.get_blacklist(context, blacklist_id)

        # Convert to APIv2 Format
        blacklist = self._view.show(context, request, blacklist)

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')
        else:
            blacklist = utils.deep_dict_merge(blacklist, body)

            # Validate the request conforms to the schema
            self._resource_schema.validate(blacklist)

            values = self._view.load(context, request, body)

            blacklist = central_api.update_blacklist(context,
                                                     blacklist_id, values)

        response.status_int = 200

        return self._view.show(context, request, blacklist)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('blacklist_id')
    def delete_one(self, blacklist_id):
        """ Delete Blacklisted Zone """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        central_api.delete_blacklist(context, blacklist_id)

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
