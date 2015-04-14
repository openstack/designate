# COPYRIGHT 2015 Hewlett-Packard Development Company, L.P.
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
from dns import zone as dnszone
from dns import exception as dnsexception
import pecan
from oslo_log import log as logging
from oslo.config import cfg

from designate.api.v2.controllers import rest
from designate import dnsutils
from designate import exceptions
from designate.objects.adapters import DesignateAdapter
from designate import policy

LOG = logging.getLogger(__name__)


class ImportController(rest.RestController):

    BASE_URI = cfg.CONF['service:api'].api_base_uri.rstrip('/')

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):

        request = pecan.request
        response = pecan.response
        context = pecan.request.environ['context']

        policy.check('zone_import', context)

        if request.content_type != 'text/dns':
            raise exceptions.UnsupportedContentType(
                'Content-type must be text/dns')

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

        zone['links']['self'] = '%s/%s/%s' % (
            self.BASE_URI, 'v2/zones', zone['id'])

        response.headers['Location'] = zone['links']['self']

        return zone
