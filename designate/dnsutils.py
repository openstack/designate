# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
import socket

import dns
import dns.zone
from dns import rdatatype
from oslo_log import log as logging

from designate import context
from designate import exceptions
from designate import objects
from designate.i18n import _LE
from designate.i18n import _LI

LOG = logging.getLogger(__name__)


class SerializationMiddleware(object):
    """DNS Middleware to serialize/deserialize DNS Packets"""

    def __init__(self, application):
        self.application = application

    def __call__(self, request):
        try:
            message = dns.message.from_wire(request['payload'])

            # Create + Attach the initial "environ" dict. This is similar to
            # the environ dict used in typical WSGI middleware.
            message.environ = {'addr': request['addr']}

        except dns.exception.DNSException:
            LOG.error(_LE("Failed to deserialize packet from %(host)s:"
                          "%(port)d") % {'host': request['addr'][0],
                                         'port': request['addr'][1]})

            # We failed to deserialize the request, generate a failure
            # response using a made up request.
            response = dns.message.make_response(
                dns.message.make_query('unknown', dns.rdatatype.A))
            response.set_rcode(dns.rcode.FORMERR)

        else:
            # Hand the Deserialized packet on
            response = self.application(message)

        # Serialize and return the response if present
        if response is not None:
            return response.to_wire()


class DNSMiddleware(object):
    """Base DNS Middleware class with some utility methods"""
    def __init__(self, application):
        self.application = application

    def process_request(self, request):
        """Called on each request.

        If this returns None, the next application down the stack will be
        executed. If it returns a response then that response will be returned
        and execution will stop here.
        """
        return None

    def process_response(self, response):
        """Do whatever you'd like to the response."""
        return response

    def __call__(self, request):
        response = self.process_request(request)

        if response:
            return response

        response = self.application(request)
        return self.process_response(response)


class ContextMiddleware(DNSMiddleware):
    """Temporary ContextMiddleware which attaches an admin context to every
    request

    This will be replaced with a piece of middleware which generates, from
    a TSIG signed request, an appropriate Request Context.
    """
    def process_request(self, request):
        ctxt = context.DesignateContext.get_admin_context(all_tenants=True)
        request.environ['context'] = ctxt

        return None


def from_dnspython_zone(dnspython_zone):
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
        'ttl': soa.ttl
    }

    zone = objects.Domain(**values)

    rrsets = dnspyrecords_to_recordsetlist(dnspython_zone.nodes)
    zone.recordsets = rrsets
    return zone


def dnspyrecords_to_recordsetlist(dnspython_records):
    rrsets = objects.RecordList()

    for rname in dnspython_records.keys():
        for rdataset in dnspython_records[rname]:
            rrset = dnspythonrecord_to_recordset(rname, rdataset)

            if rrset is None:
                continue

            rrsets.append(rrset)
    return rrsets


def dnspythonrecord_to_recordset(rname, rdataset):
    record_type = rdatatype.to_text(rdataset.rdtype)

    # Create the other recordsets
    values = {
        'name': rname.to_text(),
        'type': record_type
    }

    if rdataset.ttl != 0L:
        values['ttl'] = rdataset.ttl

    rrset = objects.RecordSet(**values)
    rrset.records = objects.RecordList()

    for rdata in rdataset:
        rr = objects.Record(data=rdata.to_text())
        rrset.records.append(rr)
    return rrset


def bind_tcp(host, port, tcp_backlog):
    # Bind to the TCP port
    LOG.info(_LI('Opening TCP Listening Socket on %(host)s:%(port)d') %
             {'host': host, 'port': port})
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock_tcp.bind((host, port))
    sock_tcp.listen(tcp_backlog)

    return sock_tcp


def bind_udp(host, port):
    # Bind to the UDP port
    LOG.info(_LI('Opening UDP Listening Socket on %(host)s:%(port)d') %
             {'host': host, 'port': port})
    sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_udp.bind((host, port))

    return sock_udp


def do_axfr(zone_name, masters):
    """
    Performs an AXFR for a given zone name
    """
    # TODO(Tim): Try the first master, try others if they exist
    master = masters[0]

    LOG.info(_LI("Doing AXFR for %(name)s from %(host)s") %
             {'name': zone_name, 'host': master})

    xfr = dns.query.xfr(master['ip'], zone_name, relativize=False,
                        port=master['port'])

    try:
        # TODO(Tim): Add a timeout to this function
        raw_zone = dns.zone.from_xfr(xfr, relativize=False)
    except Exception:
        LOG.exception(_LE("There was a problem with the AXFR"))
        raise

    LOG.debug("AXFR Successful for %s" % raw_zone.origin.to_text())

    return raw_zone
