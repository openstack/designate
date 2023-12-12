# Copyright 2015 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspae.com>
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

from designate.api.v2.controllers import rest
from designate import exceptions
from designate.objects.adapters import DesignateAdapter
from designate import utils

LOG = logging.getLogger(__name__)


class ZoneImportController(rest.RestController):

    SORT_KEYS = ['created_at', 'id', 'updated_at']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('import_id')
    def get_one(self, import_id):
        """Get Zone Imports"""

        request = pecan.request
        context = request.environ['context']

        zone_import = self.central_api.get_zone_import(
            context, import_id)

        LOG.info("Retrieved %(import)s", {'import': zone_import})

        return DesignateAdapter.render('API_v2', zone_import, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Zone Imports"""
        request = pecan.request
        context = request.environ['context']
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
                context, params, self.SORT_KEYS)

        # Extract any filter params.
        accepted_filters = ('status', 'message', 'zone_id', )

        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        zone_imports = self.central_api.find_zone_imports(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info("Retrieved %(imports)s", {'imports': zone_imports})

        return DesignateAdapter.render('API_v2', zone_imports, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create Zone Import"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body.decode('utf-8')

        if request.content_type != 'text/dns':
            raise exceptions.UnsupportedContentType(
                'Content-type must be text/dns'
            )

        # Create the zone_import
        zone_import = self.central_api.create_zone_import(
            context, body)
        response.status_int = 202

        LOG.info("Created %(zone_import)s", {'zone_import': zone_import})

        zone_import = DesignateAdapter.render('API_v2', zone_import,
                                              request=request)

        response.headers['Location'] = zone_import['links']['self']
        # Prepare and return the response body
        return zone_import

    # NOTE: template=None is important here, template='json:' manifests
    #       in this bug: https://bugs.launchpad.net/designate/+bug/1592153
    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('zone_import_id')
    def delete_one(self, zone_import_id):
        """Delete Zone Import"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        zone_import = self.central_api.delete_zone_import(
            context, zone_import_id)

        LOG.info("Deleted %(zone_import)s", {'zone_import': zone_import})

        response.status_int = 204

        return ''
