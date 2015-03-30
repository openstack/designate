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
from dns import zone as dnszone
from dns import exception as dnsexception
from oslo.config import cfg

from designate import exceptions
from designate import utils
from designate import dnsutils
from designate.api.v2.controllers import rest
from designate.api.v2.controllers import recordsets
from designate.api.v2.controllers.zones import tasks
from designate import objects
from designate.objects.adapters import DesignateAdapter


CONF = cfg.CONF


class ZonesController(rest.RestController):

    SORT_KEYS = ['created_at', 'id', 'updated_at', 'name', 'tenant_id',
                 'serial', 'ttl', 'status']

    recordsets = recordsets.RecordSetsController()
    tasks = tasks.TasksController()

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template=None, content_type='text/dns')
    @utils.validate_uuid('zone_id')
    def get_one(self, zone_id):
        """Get Zone"""
        # TODO(kiall): Validate we have a sane UUID for zone_id

        request = pecan.request
        context = request.environ['context']
        if 'Accept' not in request.headers:
            raise exceptions.BadRequest('Missing Accept header')
        best_match = request.accept.best_match(['application/json',
                                                'text/dns'])
        if best_match == 'text/dns':
            return self._get_zonefile(request, context, zone_id)
        elif best_match == 'application/json':
            return self._get_json(request, context, zone_id)
        else:
            raise exceptions.UnsupportedAccept(
                'Accept must be text/dns or application/json')

    def _get_json(self, request, context, zone_id):
        """'Normal' zone get"""
        return DesignateAdapter.render(
            'API_v2',
            self.central_api.get_domain(context, zone_id),
            request=request)

    def _get_zonefile(self, request, context, zone_id):
        """Export zonefile"""
        servers = self.central_api.get_domain_servers(context, zone_id)
        domain = self.central_api.get_domain(context, zone_id)

        criterion = {'domain_id': zone_id}
        recordsets = self.central_api.find_recordsets(context, criterion)

        records = []

        for recordset in recordsets:
            criterion = {
                'domain_id': domain['id'],
                'recordset_id': recordset['id']
            }

            raw_records = self.central_api.find_records(context, criterion)

            for record in raw_records:
                records.append({
                    'name': recordset['name'],
                    'type': recordset['type'],
                    'ttl': recordset['ttl'],
                    'data': record['data'],
                })

        return utils.render_template('bind9-zone.jinja2',
                                     servers=servers,
                                     domain=domain,
                                     records=records)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Zones"""
        request = pecan.request
        context = request.environ['context']

        marker, limit, sort_key, sort_dir = self._get_paging_params(params)

        # Extract any filter params.
        accepted_filters = ('name', 'email', 'status', )

        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.find_domains(
                context, criterion, marker, limit, sort_key, sort_dir),
            request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create Zone"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        if request.content_type == 'text/dns':
            return self._post_zonefile(request, response, context)
        elif request.content_type == 'application/json':
            return self._post_json(request, response, context)
        else:
            raise exceptions.UnsupportedContentType(
                'Content-type must be text/dns or application/json')

    def _post_json(self, request, response, context):
        """'Normal' zone creation"""
        zone = request.body_dict

        # We need to check the zone type before validating the schema since if
        # it's the type is SECONDARY we need to set the email to the mgmt email

        if isinstance(zone, dict):
            if 'type' not in zone:
                zone['type'] = 'PRIMARY'

            if zone['type'] == 'SECONDARY':
                mgmt_email = CONF['service:central'].managed_resource_email
                zone['email'] = mgmt_email

        zone = DesignateAdapter.parse('API_v2', zone, objects.Domain())

        zone.validate()

        # # TODO(ekarlso): Fix this once setter or so works.
        # masters = values.pop('masters', [])
        # zone = objects.Domain.from_dict(values)
        # zone.set_masters(masters)

        # Create the zone
        zone = self.central_api.create_domain(context, zone)

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

    def _post_zonefile(self, request, response, context):
        """Import Zone"""
        try:
            dnspython_zone = dnszone.from_text(
                request.body,
                # Don't relativize, otherwise we end up with '@' record names.
                relativize=False,
                # Dont check origin, we allow missing NS records (missing SOA
                # records are taken care of in _create_zone).
                check_origin=False)
            domain = dnsutils.from_dnspython_zone(dnspython_zone)
            domain.type = 'PRIMARY'

            for rrset in list(domain.recordsets):
                if rrset.type in ('NS', 'SOA'):
                    domain.recordsets.remove(rrset)

        except dnszone.UnknownOrigin:
            raise exceptions.BadRequest('The $ORIGIN statement is required and'
                                        ' must be the first statement in the'
                                        ' zonefile.')
        except dnsexception.SyntaxError:
            raise exceptions.BadRequest('Malformed zonefile.')

        zone = self.central_api.create_domain(context, domain)

        if zone['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201

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
        zone = self.central_api.get_domain(context, zone_id)

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
            zone = self.central_api.update_domain(
                context, zone, increment_serial=increment_serial)

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

        zone = self.central_api.delete_domain(context, zone_id)
        response.status_int = 202

        return DesignateAdapter.render('API_v2', zone, request=request)
