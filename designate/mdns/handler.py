# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import dns
import dns.flags
import dns.opcode
import dns.rcode
import dns.rdataclass
import dns.rdatatype
import dns.message
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate.mdns import xfr
from designate.central import rpcapi as central_api
from designate.i18n import _LI
from designate.i18n import _LW


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

CONF.import_opt('default_pool_id', 'designate.central',
                group='service:central')

# 10 Bytes of RR metadata, 64 bytes of TSIG RR data, variable length TSIG Key
# name (restricted in designate to 160 chars), 1 byte for trailing dot.
TSIG_RRSIZE = 10 + 64 + 160 + 1


class RequestHandler(xfr.XFRMixin):

    def __init__(self, storage, tg):
        # Get a storage connection
        self.storage = storage
        self.tg = tg

    @property
    def central_api(self):
        if not hasattr(self, '_central_api'):
            self._central_api = central_api.CentralAPI.get_instance()
        return self._central_api

    def __call__(self, request):
        """
        :param request: DNS Request Message
        :return: DNS Response Message
        """
        if request.opcode() == dns.opcode.QUERY:
            # Currently we expect exactly 1 question in the section
            # TSIG places the pseudo records into the additional section.
            if (len(request.question) != 1 or
                    request.question[0].rdclass != dns.rdataclass.IN):
                LOG.debug("Refusing due to numbers of questions or rdclass")
                yield self._handle_query_error(request, dns.rcode.REFUSED)
                raise StopIteration

            q_rrset = request.question[0]
            # Handle AXFR and IXFR requests with an AXFR responses for now.
            # It is permissible for a server to send an AXFR response when
            # receiving an IXFR request.
            if q_rrset.rdtype in (dns.rdatatype.AXFR, dns.rdatatype.IXFR):
                for response in self._handle_axfr(request):
                    yield response
                raise StopIteration

            else:
                for response in self._handle_record_query(request):
                    yield response
                raise StopIteration

        elif request.opcode() == dns.opcode.NOTIFY:
            for response in self._handle_notify(request):
                yield response
            raise StopIteration

        else:
            # Unhandled OpCode's include STATUS, IQUERY, UPDATE
            LOG.debug("Refusing unhandled opcode")
            yield self._handle_query_error(request, dns.rcode.REFUSED)
            raise StopIteration

    def _handle_notify(self, request):
        """
        Constructs the response to a NOTIFY and acts accordingly on it.

        * Checks if the master sending the NOTIFY is in the Zone's masters,
          if not it is ignored.
        * Checks if SOA query response serial != local serial.
        """
        context = request.environ['context']

        response = dns.message.make_response(request)

        if len(request.question) != 1:
            response.set_rcode(dns.rcode.FORMERR)
            yield response
            raise StopIteration
        else:
            question = request.question[0]

        criterion = {
            'name': question.name.to_text().decode('utf-8'),
            'type': 'SECONDARY',
            'deleted': False
        }

        try:
            zone = self.storage.find_zone(context, criterion)
        except exceptions.ZoneNotFound:
            response.set_rcode(dns.rcode.NOTAUTH)
            yield response
            raise StopIteration

        notify_addr = request.environ['addr'][0]

        # We check if the src_master which is the assumed master for the zone
        # that is sending this NOTIFY OP is actually the master. If it's not
        # We'll reply but don't do anything with the NOTIFY.
        master_addr = zone.get_master_by_ip(notify_addr)
        if not master_addr:
            msg = _LW("NOTIFY for %(name)s from non-master server "
                      "%(addr)s, refusing.")
            LOG.warning(msg % {"name": zone.name, "addr": notify_addr})
            response.set_rcode(dns.rcode.REFUSED)
            yield response
            raise StopIteration

        resolver = dns.resolver.Resolver()
        # According to RFC we should query the server that sent the NOTIFY
        resolver.nameservers = [notify_addr]

        soa_answer = resolver.query(zone.name, 'SOA')
        soa_serial = soa_answer[0].serial
        if soa_serial == zone.serial:
            msg = _LI("Serial %(serial)s is the same for master and us for "
                      "%(zone_id)s")
            LOG.info(msg, {"serial": soa_serial, "zone_id": zone.id})
        else:
            msg = _LI("Scheduling AXFR for %(zone_id)s from %(master_addr)s")
            info = {"zone_id": zone.id, "master_addr": master_addr}
            LOG.info(msg, info)
            self.tg.add_thread(self.zone_sync, context, zone,
                               [master_addr])

        response.flags |= dns.flags.AA

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

    def _zone_criterion_from_request(self, request, criterion=None):
        """Builds a bare criterion dict based on the request attributes"""
        criterion = criterion or {}

        tsigkey = request.environ.get('tsigkey')

        if tsigkey is None and CONF['service:mdns'].query_enforce_tsig:
            raise exceptions.Forbidden('Request is not TSIG signed')

        elif tsigkey is None:
            # Default to using the default_pool_id when no TSIG key is
            # available
            criterion['pool_id'] = CONF['service:central'].default_pool_id

        else:
            if tsigkey.scope == 'POOL':
                criterion['pool_id'] = tsigkey.resource_id

            elif tsigkey.scope == 'ZONE':
                criterion['id'] = tsigkey.resource_id

            else:
                raise NotImplementedError("Support for %s scoped TSIG Keys is "
                                          "not implemented")

        return criterion

    def _convert_to_rrset(self, zone, recordset):
        # Fetch the zone or the config ttl if the recordset ttl is null
        ttl = recordset.ttl or zone.ttl

        # construct rdata from all the records
        # TODO(Ron): this should be handled in the Storage query where we
        # find the recordsets.
        rdata = [str(record.data) for record in recordset.records
                 if record.action != 'DELETE']

        # Now put the records into dnspython's RRsets
        # answer section has 1 RR set.  If the RR set has multiple
        # records, DNSpython puts each record in a separate answer
        # section.
        # RRSet has name, ttl, class, type  and rdata
        # The rdata has one or more records
        if rdata:
            return dns.rrset.from_text_list(
                recordset.name, ttl, dns.rdataclass.IN, recordset.type, rdata)

    def _handle_axfr(self, request):
        context = request.environ['context']
        q_rrset = request.question[0]

        # First check if there is an existing zone
        # TODO(vinod) once validation is separated from the api,
        # validate the parameters
        try:
            criterion = self._zone_criterion_from_request(
                request, {'name': q_rrset.name.to_text().decode('utf-8')})
            zone = self.storage.find_zone(context, criterion)

        except exceptions.ZoneNotFound:
            LOG.warning(_LW("ZoneNotFound while handling axfr request. "
                            "Question was %(qr)s") % {'qr': q_rrset})

            yield self._handle_query_error(request, dns.rcode.REFUSED)
            raise StopIteration

        except exceptions.Forbidden:
            LOG.warning(_LW("Forbidden while handling axfr request. "
                            "Question was %(qr)s") % {'qr': q_rrset})

            yield self._handle_query_error(request, dns.rcode.REFUSED)
            raise StopIteration

        # The AXFR response needs to have a SOA at the beginning and end.
        criterion = {'zone_id': zone.id, 'type': 'SOA'}
        soa_records = self.storage.find_recordsets_axfr(context, criterion)

        # Get all the records other than SOA
        criterion = {'zone_id': zone.id, 'type': '!SOA'}
        records = self.storage.find_recordsets_axfr(context, criterion)

        # Place the SOA RRSet at the front and end of the RRSet list
        records.insert(0, soa_records[0])
        records.append(soa_records[0])

        # Build up a dummy response, we're stealing it's logic for building
        # the Flags.
        response = dns.message.make_response(request)
        response.flags |= dns.flags.AA
        response.set_rcode(dns.rcode.NOERROR)

        max_message_size = CONF['service:mdns'].max_message_size

        if max_message_size > 65535:
            LOG.warning(_LW('MDNS max message size must not be greater than '
                            '65535'))
            max_message_size = 65535

        if request.had_tsig:
            # Make some room for the TSIG RR to be appended at the end of the
            # rendered message.
            max_message_size = max_message_size - TSIG_RRSIZE

        # Render the results, yielding a packet after each TooBig exception.
        i, renderer = 0, None
        while i < len(records):
            record = records[i]

            # No renderer? Build one
            if renderer is None:
                renderer = dns.renderer.Renderer(
                    response.id, response.flags, max_message_size)
                for q in request.question:
                    renderer.add_question(q.name, q.rdtype, q.rdclass)

            # Build a DNSPython RRSet from the RR
            rrset = dns.rrset.from_text_list(
                str(record[3]),     # name
                int(record[2]) if record[2] is not None else zone.ttl,  # ttl
                dns.rdataclass.IN,  # class
                str(record[1]),     # rrtype
                [str(record[4])],   # rdata
            )

            try:
                renderer.add_rrset(dns.renderer.ANSWER, rrset)
                i += 1
            except dns.exception.TooBig:
                if renderer.counts[dns.renderer.ANSWER] == 0:
                    # We've received a TooBig from the first attempted RRSet in
                    # this packet. Log a warning and abort the AXFR.
                    LOG.warning(_LW('Aborted AXFR of %(zone)s, a single RR '
                                    '(%(rrset_type)s %(rrset_name)s) '
                                    'exceeded the max message size.'),
                                {'zone': zone.name,
                                 'rrset_type': record[1],
                                 'rrset_name': record[3]})

                    yield self._handle_query_error(request, dns.rcode.SERVFAIL)
                    raise StopIteration

                else:
                    yield self._finalize_packet(renderer, request)
                    renderer = None

        if renderer is not None:
            yield self._finalize_packet(renderer, request)

        raise StopIteration

    def _finalize_packet(self, renderer, request):
        renderer.write_header()
        if request.had_tsig:
            # Make the space we reserved for TSIG available for use
            renderer.max_size += TSIG_RRSIZE
            renderer.add_tsig(
                request.keyname,
                request.keyring[request.keyname],
                request.fudge,
                request.original_id,
                request.tsig_error,
                request.other_data,
                request.mac,
                request.keyalgorithm)
        return renderer

    def _handle_record_query(self, request):
        """Handle a DNS QUERY request for a record"""
        context = request.environ['context']
        response = dns.message.make_response(request)

        try:
            q_rrset = request.question[0]
            # TODO(vinod) once validation is separated from the api,
            # validate the parameters
            criterion = {
                'name': q_rrset.name.to_text().decode('utf-8'),
                'type': dns.rdatatype.to_text(q_rrset.rdtype),
                'zones_deleted': False
            }
            recordset = self.storage.find_recordset(context, criterion)

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
            # NXDOMAIN if it is authoritative for a zone but the FQDN doesn't
            # exist, like abcdef.rackspace.com.  Of course, a wildcard within a
            # zone would mean that NXDOMAIN isn't ever returned for a zone.
            #
            # To simply things currently this returns a REFUSED in all cases.
            # If zone transfers needs different errors, we could revisit this.
            LOG.info(_LI("NotFound, refusing. Question was %(qr)s"),
                     {'qr': q_rrset})
            yield self._handle_query_error(request, dns.rcode.REFUSED)
            raise StopIteration

        except exceptions.Forbidden:
            LOG.info(_LI("Forbidden, refusing. Question was %(qr)s"),
                     {'qr': q_rrset})
            yield self._handle_query_error(request, dns.rcode.REFUSED)
            raise StopIteration

        try:
            criterion = self._zone_criterion_from_request(
                request, {'id': recordset.zone_id})
            zone = self.storage.find_zone(context, criterion)

        except exceptions.ZoneNotFound:
            LOG.warning(_LW("ZoneNotFound while handling query request"
                            ". Question was %(qr)s") % {'qr': q_rrset})
            yield self._handle_query_error(request, dns.rcode.REFUSED)
            raise StopIteration

        except exceptions.Forbidden:
            LOG.warning(_LW("Forbidden while handling query request. "
                            "Question was %(qr)s") % {'qr': q_rrset})
            yield self._handle_query_error(request, dns.rcode.REFUSED)
            raise StopIteration

        r_rrset = self._convert_to_rrset(zone, recordset)
        response.answer = [r_rrset] if r_rrset else []
        response.set_rcode(dns.rcode.NOERROR)
        # For all the data stored in designate mdns is Authoritative
        response.flags |= dns.flags.AA
        yield response
