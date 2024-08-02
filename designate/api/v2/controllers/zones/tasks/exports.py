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
from designate.common import constants
from designate import exceptions
from designate.objects.adapters import DesignateAdapter
from designate import policy
from designate import utils

LOG = logging.getLogger(__name__)


class ZoneExportController(rest.RestController):
    @pecan.expose(template=None, content_type='text/dns')
    @utils.validate_uuid('export_id')
    def get_all(self, export_id):
        context = pecan.request.environ['context']
        target = {constants.RBAC_PROJECT_ID: context.project_id,
                  'tenant_id': context.project_id}

        policy.check('zone_export', context, target)

        export = self.central_api.get_zone_export(context, export_id)

        if export.location and export.location.startswith('designate://'):
            return self.central_api.export_zone(context, export['zone_id'])
        else:
            raise exceptions.BadRequest(
                'Zone can not be exported synchronously'
            )


class ZoneExportCreateController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Create Zone Export"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        # Create the zone_export
        zone_export = self.central_api.create_zone_export(
            context, zone_id)
        response.status_int = 202

        LOG.info("Created %(zone_export)s", {'zone_export': zone_export})

        zone_export = DesignateAdapter.render('API_v2', zone_export,
                                              request=request)

        response.headers['Location'] = zone_export['links']['self']
        return zone_export


class ZoneExportsController(rest.RestController):

    SORT_KEYS = ['created_at', 'id', 'updated_at']

    export = ZoneExportController()

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('export_id')
    def get_one(self, export_id):
        """Get Zone Exports"""

        request = pecan.request
        context = request.environ['context']

        zone_export = self.central_api.get_zone_export(context, export_id)

        LOG.info("Retrieved %(export)s", {'export': zone_export})

        return DesignateAdapter.render('API_v2', zone_export, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Zone Exports"""
        request = pecan.request
        context = request.environ['context']
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
                context, params, self.SORT_KEYS)

        # Extract any filter params.
        accepted_filters = ('status', 'message', 'zone_id', )

        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        zone_exports = self.central_api.find_zone_exports(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info("Retrieved %(exports)s",
                 {'exports': zone_exports})

        return DesignateAdapter.render('API_v2', zone_exports, request=request)

    # NOTE: template=None is important here, template='json:' manifests
    #       in this bug: https://bugs.launchpad.net/designate/+bug/1592153
    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('zone_export_id')
    def delete_one(self, zone_export_id):
        """Delete Zone Export"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        zone_export = self.central_api.delete_zone_export(
            context, zone_export_id)

        LOG.info("Deleted %(zone_export)s", {'zone_export': zone_export})

        response.status_int = 204

        return ''
