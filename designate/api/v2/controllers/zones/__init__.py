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
import pecan
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import utils
from designate.api.v2.controllers import rest
from designate.api.v2.controllers.zones import recordsets
from designate.api.v2.controllers.zones import tasks
from designate.api.v2.controllers.zones import nameservers
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI


CONF = cfg.CONF


LOG = logging.getLogger(__name__)


class ZonesController(rest.RestController):

    SORT_KEYS = ['created_at', 'id', 'updated_at', 'name', 'tenant_id',
                 'serial', 'ttl', 'status']

    recordsets = recordsets.RecordSetsController()
    tasks = tasks.TasksController()
    nameservers = nameservers.NameServersController()

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def get_one(self, zone_id):
        """Get Zone"""
        # TODO(kiall): Validate we have a sane UUID for zone_id

        request = pecan.request
        context = request.environ['context']

        zone = self.central_api.get_zone(context, zone_id)

        LOG.info(_LI("Retrieved %(zone)s"), {'zone': zone})

        return DesignateAdapter.render(
            'API_v2',
            zone,
            request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Zones"""
        request = pecan.request
        context = request.environ['context']

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
                context, params, self.SORT_KEYS)

        # Extract any filter params.
        accepted_filters = ('name', 'type', 'email', 'status',
                            'description', 'ttl', )

        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        zones = self.central_api.find_zones(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info(_LI("Retrieved %(zones)s"), {'zones': zones})

        return DesignateAdapter.render('API_v2', zones, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create Zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        zone = request.body_dict

        if isinstance(zone, dict):
            if 'type' not in zone:
                zone['type'] = 'PRIMARY'

        zone = DesignateAdapter.parse('API_v2', zone, objects.Zone())
        zone.validate()

        if zone.type == 'SECONDARY':
            mgmt_email = CONF['service:central'].managed_resource_email
            zone['email'] = mgmt_email

        # Create the zone
        zone = self.central_api.create_zone(context, zone)

        LOG.info(_LI("Created %(zone)s"), {'zone': zone})

        # Prepare the response headers
        # If the zone has been created asynchronously

        if zone['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201

        # Prepare and return the response body
        zone = DesignateAdapter.render('API_v2', zone, request=request)

        response.headers['Location'] = zone['links']['self']

        return zone

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('zone_id')
    def patch_one(self, zone_id):
        """Update Zone"""
        # TODO(kiall): This needs cleanup to say the least..
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # TODO(kiall): Validate we have a sane UUID for zone_id

        # Fetch the existing zone
        zone = self.central_api.get_zone(context, zone_id)

        # Don't allow updates to zones that are being deleted
        if zone.action == "DELETE":
            raise exceptions.BadRequest('Can not update a deleting zone')

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
            # Update the zone object with the new values
            zone = DesignateAdapter.parse('API_v2', body, zone)

            zone.validate()
            # If masters are specified then we set zone.transferred_at to None
            # which will cause a new transfer
            if 'attributes' in zone.obj_what_changed():
                zone.transferred_at = None

            # Update and persist the resource

            if zone.type == 'SECONDARY' and 'email' in zone.obj_what_changed():
                msg = "Changed email is not allowed."
                raise exceptions.InvalidObject(msg)

            increment_serial = zone.type == 'PRIMARY'
            zone = self.central_api.update_zone(
                context, zone, increment_serial=increment_serial)

        LOG.info(_LI("Updated %(zone)s"), {'zone': zone})

        if zone.status == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 200

        return DesignateAdapter.render('API_v2', zone, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def delete_one(self, zone_id):
        """Delete Zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        zone = self.central_api.delete_zone(context, zone_id)
        response.status_int = 202

        LOG.info(_LI("Deleted %(zone)s"), {'zone': zone})

        return DesignateAdapter.render('API_v2', zone, request=request)
