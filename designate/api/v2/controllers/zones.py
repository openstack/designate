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
from dns import rdatatype
from dns import exception as dnsexception
from designate import exceptions
from designate import utils
from designate import schema
from designate.api.v2.controllers import rest
from designate.api.v2.controllers import recordsets
from designate.api.v2.views import zones as zones_view
from designate.central import rpcapi as central_rpcapi
from designate.openstack.common import log as logging

LOG = logging.getLogger(__name__)
central_api = central_rpcapi.CentralAPI()


class ZonesController(rest.RestController):
    _view = zones_view.ZonesView()
    _resource_schema = schema.Schema('v2', 'zone')
    _collection_schema = schema.Schema('v2', 'zones')

    recordsets = recordsets.RecordSetsController()

    @pecan.expose(template=None, content_type='text/dns')
    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, zone_id):
        """ Get Zone """
        # TODO(kiall): Validate we have a sane UUID for zone_id

        request = pecan.request
        context = request.environ['context']
        if 'Accept' not in request.headers:
            raise exceptions.BadRequest('Missing Accept header')
        best_match = request.accept.best_match(['text/dns',
                                                'application/json'])
        if best_match == 'text/dns':
            return self._get_zonefile(request, context, zone_id)
        elif best_match == 'application/json':
            return self._get_json(request, context, zone_id)
        else:
            raise exceptions.UnsupportedAccept(
                'Accept must be text/dns or application/json')

    def _get_json(self, request, context, zone_id):
        """ 'Normal' zone get """
        zone = central_api.get_domain(context, zone_id)

        return self._view.detail(context, request, zone)

    def _get_zonefile(self, request, context, zone_id):
        """ Export zonefile """
        servers = central_api.get_domain_servers(context, zone_id)
        domain = central_api.get_domain(context, zone_id)
        records = central_api.find_records(context, zone_id)
        return utils.render_template('bind9-zone.jinja2',
                                     servers=servers,
                                     domain=domain,
                                     records=records)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """ List Zones """
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        #marker = params.pop('marker', None)
        #limit = int(params.pop('limit', 30))

        # Extract any filter params.
        accepted_filters = ('name', 'email')
        criterion = dict((k, params[k]) for k in accepted_filters
                         if k in params)

        zones = central_api.find_domains(context, criterion)

        return self._view.list(context, request, zones)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """ Create Zone """
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
        """ 'Normal' zone creation """
        body = request.body_dict

        # Validate the request conforms to the schema
        self._resource_schema.validate(body)

        # Convert from APIv2 -> Central format
        values = self._view.load(context, request, body)

        # Create the zone
        zone = central_api.create_domain(context, values)

        # Prepare the response headers
        # If the zone has been created asynchronously

        if zone['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(request,
                                                                     zone)

        # Prepare and return the response body
        return self._view.detail(context, request, zone)

    def _post_zonefile(self, request, response, context):
        """ Import Zone """
        dnspython_zone = self._parse_zonefile(request)
        # TODO(artom) This should probably be handled with transactions
        zone = self._create_zone(context, dnspython_zone)

        try:
            self._create_records(context, zone['id'], dnspython_zone)

        except exceptions.Base as e:
            central_api.delete_domain(context, zone['id'])
            raise e

        if zone['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 201

        response.headers['Location'] = self._view._get_resource_href(request,
                                                                     zone)
        return self._view.detail(context, request, zone)

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    def patch_one(self, zone_id):
        """ Update Zone """
        # TODO(kiall): This needs cleanup to say the least..
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # TODO(kiall): Validate we have a sane UUID for zone_id

        # Fetch the existing zone
        zone = central_api.get_domain(context, zone_id)

        # Convert to APIv2 Format
        zone = self._view.detail(context, request, zone)

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
            zone = utils.deep_dict_merge(zone, body)

            # Validate the request conforms to the schema
            self._resource_schema.validate(zone)

            values = self._view.load(context, request, body)
            zone = central_api.update_domain(context, zone_id, values)

        if zone['status'] == 'PENDING':
            response.status_int = 202
        else:
            response.status_int = 200

        return self._view.detail(context, request, zone)

    @pecan.expose(template=None, content_type='application/json')
    def delete_one(self, zone_id):
        """ Delete Zone """
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        # TODO(kiall): Validate we have a sane UUID for zone_id

        zone = central_api.delete_domain(context, zone_id)

        if zone['status'] == 'DELETING':
            response.status_int = 202
        else:
            response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''

    #TODO(artom) Methods below may be useful elsewhere, consider putting them
    # somewhere reusable.

    def _create_zone(self, context, dnspython_zone):
        """ Creates the initial zone """
        # dnspython never builds a zone with more than one SOA, even if we give
        # it a zonefile that contains more than one
        soa = dnspython_zone.get_rdataset(dnspython_zone.origin, 'SOA')
        if soa is None:
            raise exceptions.BadRequest('An SOA record is required')
        email = soa[0].rname.to_text().rstrip('.')
        email = email.replace('.', '@', 1)
        values = {
            'name': dnspython_zone.origin.to_text(),
            'email': email,
            'ttl': str(soa.ttl)
        }
        return central_api.create_domain(context, values)

    def _record2json(self, record_type, rdata):
        if record_type == 'MX':
            return {
                'type': record_type,
                'data': rdata.exchange.to_text(),
                'priority': str(rdata.preference)
            }
        elif record_type == 'SRV':
            return {
                'type': record_type,
                'data': '%s %s %s' % (str(rdata.weight), str(rdata.port),
                                      rdata.target.to_text()),
                'priority': str(rdata.priority)
            }
        else:
            return {
                'type': record_type,
                'data': rdata.to_text()
            }

    def _create_records(self, context, zone_id, dnspython_zone):
        """ Creates the records """
        for record_name in dnspython_zone.nodes.keys():
            for rdataset in dnspython_zone.nodes[record_name]:
                record_type = rdatatype.to_text(rdataset.rdtype)
                for rdata in rdataset:
                    if record_type == 'SOA':
                        # Don't create SOA records
                        pass
                    elif (record_type == 'NS'
                          and record_name == dnspython_zone.origin):
                        # Don't create NS records for the domain, they've been
                        # taken care of as servers
                        pass
                    else:
                        # Everything else, including delegation NS, gets
                        # created
                        values = self._record2json(record_type, rdata)
                        values['name'] = record_name.to_text()
                        central_api.create_record(context, zone_id, values)

    def _parse_zonefile(self, request):
        """ Parses a POSTed zonefile into a dnspython zone object """
        try:
            dnspython_zone = dnszone.from_text(
                request.body,
                # Don't relativize, otherwise we end up with '@' record names.
                relativize=False,
                # Dont check origin, we allow missing NS records (missing SOA
                # records are taken care of in _create_zone).
                check_origin=False)
        except dnszone.UnknownOrigin:
            raise exceptions.BadRequest('The $ORIGIN statement is required and'
                                        ' must be the first statement in the'
                                        ' zonefile.')
        except dnsexception.SyntaxError:
            raise exceptions.BadRequest('Malformed zonefile.')
        return dnspython_zone
