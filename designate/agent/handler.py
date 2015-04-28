# Copyright 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
import dns
import dns.opcode
import dns.rcode
import dns.message
import dns.flags
import dns.opcode
from oslo_config import cfg
from oslo_log import log as logging

from designate import utils
from designate import dnsutils
from designate.backend import agent_backend
from designate.i18n import _LW
from designate.i18n import _LI


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

# Command and Control OPCODE
CC = 14

# Private DNS CLASS Uses
ClassCC = 65280

# Private RR Code Uses
SUCCESS = 65280
FAILURE = 65281
CREATE = 65282
DELETE = 65283


class RequestHandler(object):
    def __init__(self):
        self.masters = []
        for server in CONF['service:agent'].masters:
            raw_server = utils.split_host_port(server)
            master = {'ip': raw_server[0], 'port': int(raw_server[1])}
            self.masters.append(master)

        LOG.info(_LI("Agent masters: %(masters)s") %
                 {'masters': self.masters})

        self.allow_notify = CONF['service:agent'].allow_notify
        self.transfer_source = CONF['service:agent'].transfer_source
        backend_driver = cfg.CONF['service:agent'].backend_driver
        self.backend = agent_backend.get_backend(backend_driver, self)

    def __call__(self, request):
        """
        :param request: DNS Request Message
        :return: DNS Response Message
        """
        # TODO(Tim): Handle multiple questions
        rdtype = request.question[0].rdtype
        rdclass = request.question[0].rdclass
        opcode = request.opcode()
        if opcode == dns.opcode.NOTIFY:
            response = self._handle_notify(request)
        elif opcode == CC:
            if rdclass == ClassCC:
                if rdtype == CREATE:
                    response = self._handle_create(request)
                elif rdtype == DELETE:
                    response = self._handle_delete(request)
                else:
                    response = self._handle_query_error(request,
                                                        dns.rcode.REFUSED)
            else:
                response = self._handle_query_error(request, dns.rcode.REFUSED)
        else:
            # Unhandled OpCodes include STATUS, QUERY, IQUERY, UPDATE
            response = self._handle_query_error(request, dns.rcode.REFUSED)

        # TODO(Tim): Answer Type 65XXX queries
        yield response
        raise StopIteration

    def _handle_query_error(self, request, rcode):
        """
        Construct an error response with the rcode passed in.
        :param request: The decoded request from the wire.
        :param rcode: The response code to send back.
        :return: A dns response message with the response code set to rcode
        """
        response = dns.message.make_response(request)
        response.set_rcode(rcode)

        return response

    def _handle_create(self, request):
        response = dns.message.make_response(request)

        question = request.question[0]
        requester = request.environ['addr'][0]
        domain_name = question.name.to_text()

        if not self._allowed(request, requester, "CREATE", domain_name):
            response.set_rcode(dns.rcode.from_text("REFUSED"))
            return response

        serial = self.backend.find_domain_serial(domain_name)

        if serial is not None:
            LOG.warn(_LW("Not creating %(name)s, zone already exists") %
                 {'name': domain_name})
            # Provide an authoritative answer
            response.flags |= dns.flags.AA
            return response

        LOG.debug("Received %(verb)s for %(name)s from %(host)s" %
                 {'verb': "CREATE", 'name': domain_name, 'host': requester})

        try:
            zone = dnsutils.do_axfr(domain_name, self.masters,
                source=self.transfer_source)
            self.backend.create_domain(zone)
        except Exception:
            response.set_rcode(dns.rcode.from_text("SERVFAIL"))
            return response

        # Provide an authoritative answer
        response.flags |= dns.flags.AA

        return response

    def _handle_notify(self, request):
        """
        Constructs the response to a NOTIFY and acts accordingly on it.

        * Decodes the NOTIFY
        * Checks if the master sending the NOTIFY is allowed to notify
        * Does a serial check to see if further action needs to be taken
        * Kicks off an AXFR and returns a valid response
        """
        response = dns.message.make_response(request)

        question = request.question[0]
        requester = request.environ['addr'][0]
        domain_name = question.name.to_text()

        if not self._allowed(request, requester, "NOTIFY", domain_name):
            response.set_rcode(dns.rcode.from_text("REFUSED"))
            return response

        serial = self.backend.find_domain_serial(domain_name)

        if serial is None:
            LOG.warn(_LW("Refusing NOTIFY for %(name)s, doesn't exist") %
                 {'name': domain_name})
            response.set_rcode(dns.rcode.from_text("REFUSED"))
            return response

        LOG.debug("Received %(verb)s for %(name)s from %(host)s" %
                 {'verb': "NOTIFY", 'name': domain_name, 'host': requester})

        # According to RFC we should query the server that sent the NOTIFY
        # TODO(Tim): Reenable this when it makes more sense
        # resolver = dns.resolver.Resolver()
        # resolver.nameservers = [requester]
        # This assumes that the Master is running on port 53
        # soa_answer = resolver.query(domain_name, 'SOA')
        # Check that the serial is < serial above

        try:
            zone = dnsutils.do_axfr(domain_name, self.masters,
                source=self.transfer_source)
            self.backend.update_domain(zone)
        except Exception:
            response.set_rcode(dns.rcode.from_text("SERVFAIL"))
            return response

        # Provide an authoritative answer
        response.flags |= dns.flags.AA

        return response

    def _handle_delete(self, request):
        """
        Constructs the response to a DELETE and acts accordingly on it.

        * Decodes the message for zone name
        * Checks if the master sending the DELETE is in the allowed notify list
        * Checks if the zone exists (maybe?)
        * Kicks a call to the backend to delete the zone in question
        """
        response = dns.message.make_response(request)

        question = request.question[0]
        requester = request.environ['addr'][0]
        domain_name = question.name.to_text()

        if not self._allowed(request, requester, "DELETE", domain_name):
            response.set_rcode(dns.rcode.from_text("REFUSED"))
            return response

        serial = self.backend.find_domain_serial(domain_name)

        if serial is None:
            LOG.warn(_LW("Not deleting %(name)s, zone doesn't exist") %
                 {'name': domain_name})
            # Provide an authoritative answer
            response.flags |= dns.flags.AA
            return response

        LOG.debug("Received DELETE for %(name)s from %(host)s" %
                 {'name': domain_name, 'host': requester})

        # Provide an authoritative answer
        response.flags |= dns.flags.AA

        # Call into the backend to Delete
        try:
            self.backend.delete_domain(domain_name)
        except Exception:
            response.set_rcode(dns.rcode.from_text("SERVFAIL"))
            return response

        return response

    def _allowed(self, request, requester, op, domain_name):
        if requester not in self.allow_notify:
            LOG.warn(_LW("%(verb)s for %(name)s from %(server)s refused") %
            {'verb': op, 'name': domain_name, 'server': requester})
            return False

        return True
