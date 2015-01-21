# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import dns
from oslo.config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import storage
from designate.i18n import _LE


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class RequestHandler(object):
    def __init__(self):
        # Get a storage connection
        storage_driver = cfg.CONF['service:mdns'].storage_driver
        self.storage = storage.get_storage(storage_driver)

    def __call__(self, request):
        """
        :param request: DNS Request Message
        :return: DNS Response Message
        """
        context = request.environ['context']

        if request.opcode() == dns.opcode.QUERY:
            # Currently we expect exactly 1 question in the section
            # TSIG places the pseudo records into the additional section.
            if (len(request.question) != 1 or
                    request.question[0].rdclass != dns.rdataclass.IN):
                return self._handle_query_error(request, dns.rcode.REFUSED)

            q_rrset = request.question[0]
            # Handle AXFR and IXFR requests with an AXFR responses for now.
            # It is permissible for a server to send an AXFR response when
            # receiving an IXFR request.
            # TODO(Ron): send IXFR response when receiving IXFR request.
            if q_rrset.rdtype in (dns.rdatatype.AXFR, dns.rdatatype.IXFR):
                response = self._handle_axfr(context, request)
            else:
                response = self._handle_record_query(context, request)
        else:
            # Unhandled OpCode's include STATUS, IQUERY, NOTIFY, UPDATE
            response = self._handle_query_error(request, dns.rcode.REFUSED)

        return response

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

    def _convert_to_rrset(self, context, recordset, domain=None):
        # Fetch the domain or the config ttl if the recordset ttl is null
        if recordset.ttl:
            ttl = recordset.ttl
        elif domain is not None:
            ttl = domain.ttl
        else:
            domain = self.storage.get_domain(context, recordset.domain_id)
            if domain.ttl:
                ttl = domain.ttl
            else:
                ttl = CONF.default_ttl

        # construct rdata from all the records
        rdata = []
        for record in recordset.records:
            # TODO(Ron): this should be handled in the Storage query where we
            # find the recordsets.
            if record.action != 'DELETE':
                rdata.append(str(record.data))

        # Now put the records into dnspython's RRsets
        # answer section has 1 RR set.  If the RR set has multiple
        # records, DNSpython puts each record in a separate answer
        # section.
        # RRSet has name, ttl, class, type  and rdata
        # The rdata has one or more records
        r_rrset = None
        if rdata:
            r_rrset = dns.rrset.from_text_list(
                recordset.name, ttl, dns.rdataclass.IN, recordset.type, rdata)

        return r_rrset

    def _handle_axfr(self, context, request):
        response = dns.message.make_response(request)
        q_rrset = request.question[0]
        # First check if there is an existing zone
        # TODO(vinod) once validation is separated from the api,
        # validate the parameters
        criterion = {'name': q_rrset.name.to_text()}
        try:
            domain = self.storage.find_domain(context, criterion)
        except exceptions.DomainNotFound:
            LOG.exception(_LE("got exception while handling axfr request. "
                              "Question is %(qr)s") % {'qr': q_rrset})

            return self._handle_query_error(request, dns.rcode.REFUSED)

        r_rrsets = []

        # The AXFR response needs to have a SOA at the beginning and end.
        criterion = {'domain_id': domain.id, 'type': 'SOA'}
        soa_recordsets = self.storage.find_recordsets(context, criterion)

        for recordset in soa_recordsets:
            r_rrsets.append(self._convert_to_rrset(context, recordset, domain))

        # Get all the recordsets other than SOA
        criterion = {'domain_id': domain.id, 'type': '!SOA'}
        recordsets = self.storage.find_recordsets(context, criterion)

        for recordset in recordsets:
            r_rrset = self._convert_to_rrset(context, recordset, domain)
            if r_rrset:
                r_rrsets.append(r_rrset)

        # Append the SOA recordset at the end
        for recordset in soa_recordsets:
            r_rrsets.append(self._convert_to_rrset(context, recordset, domain))

        response.set_rcode(dns.rcode.NOERROR)
        # TODO(vinod) check if we dnspython has an upper limit on the number
        # of rrsets.
        response.answer = r_rrsets
        # For all the data stored in designate mdns is Authoritative
        response.flags |= dns.flags.AA

        return response

    def _handle_record_query(self, context, request):
        """Handle a DNS QUERY request for a record"""
        response = dns.message.make_response(request)
        try:
            q_rrset = request.question[0]
            # TODO(vinod) once validation is separated from the api,
            # validate the parameters
            criterion = {
                'name': q_rrset.name.to_text(),
                'type': dns.rdatatype.to_text(q_rrset.rdtype),
                'domains_deleted': False
            }
            recordset = self.storage.find_recordset(context, criterion)
            r_rrset = self._convert_to_rrset(context, recordset)
            response.set_rcode(dns.rcode.NOERROR)
            response.answer = [r_rrset]
            # For all the data stored in designate mdns is Authoritative
            response.flags |= dns.flags.AA
        except exceptions.NotFound:
            # If an FQDN exists, like www.rackspace.com, but the specific
            # record type doesn't exist, like type SPF, then the return code
            # would be NOERROR and the SOA record is returned.  This tells
            # caching nameservers that the FQDN does exist, so don't negatively
            # cache it, but the specific record doesn't exist.
            #
            # If an FQDN doesn't exist with any record type, that is NXDOMAIN.
            # However, an authoritative nameserver shouldn't return NXDOMAIN
            # for a zone it isn't authoritative for.  It would be more
            # appropriate for it to return REFUSED.  It should still return
            # NXDOMAIN if it is authoritative for a domain but the FQDN doesn't
            # exist, like abcdef.rackspace.com.  Of course, a wildcard within a
            # domain would mean that NXDOMAIN isn't ever returned for a domain.
            #
            # To simply things currently this returns a REFUSED in all cases.
            # If zone transfers needs different errors, we could revisit this.
            response.set_rcode(dns.rcode.REFUSED)

        return response
