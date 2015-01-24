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
import struct

import dns
import dns.zone
from dns import rdatatype
from oslo_log import log as logging

from designate import exceptions
from designate import objects
from designate.i18n import _LE
from designate.i18n import _LI
from designate.i18n import _LW

LOG = logging.getLogger(__name__)


class DNSMiddleware(object):
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


def _deserialize_request(payload, addr):
    """
    Deserialize a DNS Request Packet

    :param payload: Raw DNS query payload
    :param addr: Tuple of the client's (IP, Port)
    """
    try:
        request = dns.message.from_wire(payload)
    except dns.exception.DNSException:
        LOG.error(_LE("Failed to deserialize packet from %(host)s:%(port)d") %
                  {'host': addr[0], 'port': addr[1]})
        return None
    else:
        # Create + Attach the initial "environ" dict. This is similar to
        # the environ dict used in typical WSGI middleware.
        request.environ = {'addr': addr}
        return request


def _serialize_response(response):
    """
    Serialize a DNS Response Packet

    :param response: DNS Response Message
    """
    return response.to_wire()


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


def handle_tcp(sock_tcp, tg, handle, application, timeout=None):
    LOG.info(_LI("_handle_tcp thread started"))
    while True:
        client, addr = sock_tcp.accept()
        if timeout:
            client.settimeout(timeout)

        LOG.debug("Handling TCP Request from: %(host)s:%(port)d" %
                 {'host': addr[0], 'port': addr[1]})

        # Prepare a variable for the payload to be buffered
        payload = ""

        try:
            # Receive the first 2 bytes containing the payload length
            expected_length_raw = client.recv(2)
            (expected_length, ) = struct.unpack('!H', expected_length_raw)

            # Keep receiving data until we've got all the data we expect
            while len(payload) < expected_length:
                data = client.recv(65535)
                if not data:
                    break
                payload += data

        except socket.timeout:
            client.close()
            LOG.warn(_LW("TCP Timeout from: %(host)s:%(port)d") %
                     {'host': addr[0], 'port': addr[1]})

        # Dispatch a thread to handle the query
        tg.add_thread(handle, addr, payload, application, client=client)


def handle_udp(sock_udp, tg, handle, application):
    LOG.info(_LI("_handle_udp thread started"))
    while True:
        # TODO(kiall): Determine the appropriate default value for
        #              UDP recvfrom.
        payload, addr = sock_udp.recvfrom(8192)
        LOG.debug("Handling UDP Request from: %(host)s:%(port)d" %
                 {'host': addr[0], 'port': addr[1]})

        tg.add_thread(handle, addr, payload, application, sock_udp=sock_udp)


def handle(addr, payload, application, sock_udp=None, client=None):
    """
    Handle a DNS Query

    :param addr: Tuple of the client's (IP, Port)
    :param payload: Raw DNS query payload
    :param client: Client socket (for TCP only)
    """
    try:
        request = _deserialize_request(payload, addr)

        if request is None:
            # We failed to deserialize the request, generate a failure
            # response using a made up request.
            response = dns.message.make_response(
                dns.message.make_query('unknown', dns.rdatatype.A))
            response.set_rcode(dns.rcode.FORMERR)
        else:
            response = application(request)

        # send back a response only if present
        if response:
            response = _serialize_response(response)

            if client:
                # Handle TCP Responses
                msg_length = len(response)
                tcp_response = struct.pack("!H", msg_length) + response
                client.send(tcp_response)
                client.close()
            elif sock_udp:
                # Handle UDP Responses
                sock_udp.sendto(response, addr)
            else:
                LOG.warn(_LW("Both sock_udp and client are None"))
    except Exception:
        LOG.exception(_LE("Unhandled exception while processing request "
                          "from %(host)s:%(port)d") %
                      {'host': addr[0], 'port': addr[1]})


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
