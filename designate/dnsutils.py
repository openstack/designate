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
import random
import socket
import base64

import dns
import dns.exception
import dns.zone
import eventlet
from dns import rdatatype
from oslo_log import log as logging
from oslo.config import cfg

from designate import context
from designate import exceptions
from designate import utils
from designate import objects
from designate.i18n import _LE
from designate.i18n import _LI

LOG = logging.getLogger(__name__)


util_opts = [
    cfg.IntOpt('xfr_timeout', help="Timeout in seconds for XFR's.", default=10)
]


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

    def _build_error_response(self):
        response = dns.message.make_response(
            dns.message.make_query('unknown', dns.rdatatype.A))
        response.set_rcode(dns.rcode.FORMERR)

        return response


class SerializationMiddleware(DNSMiddleware):
    """DNS Middleware to serialize/deserialize DNS Packets"""

    def __init__(self, application, tsig_keyring=None):
        self.application = application
        self.tsig_keyring = tsig_keyring

    def __call__(self, request):
        # Generate the initial context. This may be updated by other middleware
        # as we learn more information about the Request.
        ctxt = context.DesignateContext.get_admin_context(all_tenants=True)

        try:
            message = dns.message.from_wire(request['payload'],
                                            self.tsig_keyring)

            if message.had_tsig:
                LOG.debug('Request signed with TSIG key: %s', message.keyname)

            # Create + Attach the initial "environ" dict. This is similar to
            # the environ dict used in typical WSGI middleware.
            message.environ = {
                'context': ctxt,
                'addr': request['addr'],
            }

        except dns.message.UnknownTSIGKey:
            LOG.error(_LE("Unknown TSIG key from %(host)s:"
                          "%(port)d") % {'host': request['addr'][0],
                                         'port': request['addr'][1]})

            response = self._build_error_response()

        except dns.tsig.BadSignature:
            LOG.error(_LE("Invalid TSIG signature from %(host)s:"
                          "%(port)d") % {'host': request['addr'][0],
                                         'port': request['addr'][1]})

            response = self._build_error_response()

        except dns.exception.DNSException:
            LOG.error(_LE("Failed to deserialize packet from %(host)s:"
                          "%(port)d") % {'host': request['addr'][0],
                                         'port': request['addr'][1]})

            response = self._build_error_response()

        else:
            # Hand the Deserialized packet onto the Application
            for response in self.application(message):
                # Serialize and return the response if present
                if isinstance(response, dns.message.Message):
                    yield response.to_wire(max_size=65535)

                elif isinstance(response, dns.renderer.Renderer):
                    yield response.get_wire()


class TsigInfoMiddleware(DNSMiddleware):
    """Middleware which looks up the information available for a TsigKey"""

    def __init__(self, application, storage):
        super(TsigInfoMiddleware, self).__init__(application)

        self.storage = storage

    def process_request(self, request):
        if not request.had_tsig:
            return None

        try:
            criterion = {'name': request.keyname.to_text(True)}
            tsigkey = self.storage.find_tsigkey(
                    context.get_current(), criterion)

            request.environ['tsigkey'] = tsigkey
            request.environ['context'].tsigkey_id = tsigkey.id

        except exceptions.TsigKeyNotFound:
            # This should never happen, as we just validated the key.. Except
            # for race conditions..
            return self._build_error_response()

        return None


class TsigKeyring(object):
    """Implements the DNSPython KeyRing API, backed by the Designate DB"""

    def __init__(self, storage):
        self.storage = storage

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, default=None):
        try:
            criterion = {'name': key.to_text(True)}
            tsigkey = self.storage.find_tsigkey(
                context.get_current(), criterion)

            return base64.decodestring(tsigkey.secret)

        except exceptions.TsigKeyNotFound:
            return default


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
        'ttl': soa.ttl,
        'serial': soa[0].serial,
        'retry': soa[0].retry,
        'expire': soa[0].expire
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
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock_tcp.setblocking(True)
    sock_tcp.bind((host, port))
    sock_tcp.listen(tcp_backlog)

    return sock_tcp


def bind_udp(host, port):
    # Bind to the UDP port
    LOG.info(_LI('Opening UDP Listening Socket on %(host)s:%(port)d') %
             {'host': host, 'port': port})
    sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock_udp.setblocking(True)
    sock_udp.bind((host, port))

    return sock_udp


def expand_servers(servers):
    """
    Expands list of server:port into a list of dicts.

    Example: [{"host": ..., "port": 53}]
    """
    data = []
    for srv in servers:
        if isinstance(srv, basestring):
            host, port = utils.split_host_port(srv, 53)
        srv = {"ip": host, "port": port}
        data.append(srv)

    return data


def do_axfr(zone_name, servers, timeout=None, source=None):
    """
    Performs an AXFR for a given zone name
    """
    random.shuffle(servers)
    timeout = timeout or 10

    xfr = None
    for srv in servers:
        timeout = eventlet.Timeout(timeout)
        log_info = {'name': zone_name, 'host': srv}
        try:
            LOG.info(_LI("Doing AXFR for %(name)s from %(host)s") % log_info)
            xfr = dns.query.xfr(srv['ip'], zone_name, relativize=False,
                                timeout=1, port=srv['port'], source=source)
            raw_zone = dns.zone.from_xfr(xfr, relativize=False)
            break
        except eventlet.Timeout as t:
            if t == timeout:
                msg = _LE("AXFR timed out for %(name)s from %(host)s")
                LOG.error(msg % log_info)
                continue
        except dns.exception.FormError:
            msg = _LE("Domain %(name)s is not present on %(host)s."
                      "Trying next server.")
            LOG.error(msg % log_info)
        except socket.error:
            msg = _LE("Connection error when doing AXFR for %(name)s from "
                      "%(host)s")
            LOG.error(msg % log_info)
        except Exception:
            msg = _LE("Problem doing AXFR %(name)s from %(host)s. "
                      "Trying next server.")
            LOG.exception(msg % log_info)
        finally:
            timeout.cancel()
        continue
    else:
        msg = _LE("XFR failed for %(name)s. No servers in %(servers)s was "
                  "reached.")
        raise exceptions.XFRFailure(
            msg % {"name": zone_name, "servers": servers})

    LOG.debug("AXFR Successful for %s" % raw_zone.origin.to_text())

    return raw_zone
