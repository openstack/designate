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
from oslo_log import log as logging
import pecan

from designate.api.v2.controllers import rest
from designate.objects.adapters import DesignateAdapter
from designate.objects import Tld
from designate import utils

LOG = logging.getLogger(__name__)


class TldsController(rest.RestController):
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'name']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('tld_id')
    def get_one(self, tld_id):
        """Get Tld"""

        request = pecan.request
        context = request.environ['context']

        tld = self.central_api.get_tld(context, tld_id)

        LOG.info("Retrieved %(tld)s", {'tld': tld})

        return DesignateAdapter.render('API_v2', tld, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Tlds"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
                context, params, self.SORT_KEYS)

        # Extract any filter params.
        accepted_filters = ('name', )
        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        tlds = self.central_api.find_tlds(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info("Retrieved %(tlds)s", {'tlds': tlds})

        return DesignateAdapter.render('API_v2', tlds, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create Tld"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        tld = DesignateAdapter.parse('API_v2', body, Tld())

        tld.validate()

        # Create the tld
        tld = self.central_api.create_tld(context, tld)

        LOG.info("Created %(tld)s", {'tld': tld})

        response.status_int = 201

        tld = DesignateAdapter.render('API_v2', tld, request=request)

        response.headers['Location'] = tld['links']['self']

        # Prepare and return the response body
        return tld

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('tld_id')
    def patch_one(self, tld_id):
        """Update Tld"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response
        if request.content_type == 'application/json-patch+json':
            raise NotImplementedError('json-patch not implemented')

        # Fetch the existing tld
        tld = self.central_api.get_tld(context, tld_id)

        tld = DesignateAdapter.parse('API_v2', body, tld)

        tld.validate()

        tld = self.central_api.update_tld(context, tld)

        LOG.info("Updated %(tld)s", {'tld': tld})

        response.status_int = 200

        return DesignateAdapter.render('API_v2', tld, request=request)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('tld_id')
    def delete_one(self, tld_id):
        """Delete Tld"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        tld = self.central_api.delete_tld(context, tld_id)

        LOG.info("Deleted %(tld)s", {'tld': tld})

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
