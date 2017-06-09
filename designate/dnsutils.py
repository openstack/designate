# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
import time
from threading import Lock

import six
import dns
import dns.exception
import dns.zone
import eventlet
from dns import rdatatype
from oslo_log import log as logging
from oslo_config import cfg

from designate import context
from designate import exceptions
from designate import objects
from designate.i18n import _LE
from designate.i18n import _LI

LOG = logging.getLogger(__name__)


util_opts = [
    cfg.IntOpt('xfr_timeout', help="Timeout in seconds for XFR's.", default=10)
]

cfg.CONF.register_opts(util_opts)


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

        except Exception:
            LOG.exception(_LE("Unknown exception deserializing packet "
                          "from %(host)s %(port)d") %
                          {'host': request['addr'][0],
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

                else:
                    LOG.error(_LE("Unexpected response %(resp)s") %
                              repr(response))


class TsigInfoMiddleware(DNSMiddleware):
    """Middleware which looks up the information available for a TsigKey"""

    def __init__(self, application, storage):
        super(TsigInfoMiddleware, self).__init__(application)

        self.storage = storage

    def process_request(self, request):
        if not request.had_tsig:
            return None

        try:
            criterion = {'name': request.keyname.to_text(True).decode('utf-8')}
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
            criterion = {'name': key.to_text(True).decode('utf-8')}
            tsigkey = self.storage.find_tsigkey(
                context.get_current(), criterion)

            return base64.decodestring(tsigkey.secret)

        except exceptions.TsigKeyNotFound:
            return default


class ZoneLock(object):
    """A Lock across all zones that enforces a rate limit on NOTIFYs"""

    def __init__(self, delay):
        self.lock = Lock()
        self.data = {}
        self.delay = delay

    def acquire(self, zone):
        with self.lock:
            # If no one holds the lock for the zone, grant it
            if zone not in self.data:
                self.data[zone] = time.time()
                return True

            # Otherwise, get the time that it was locked
            locktime = self.data[zone]
            now = time.time()

            period = now - locktime

            # If it has been locked for longer than the allowed period
            # give the lock to the new requester
            if period > self.delay:
                self.data[zone] = now
                return True

            LOG.debug('Lock for %(zone)s can\'t be released for %(period)s'
                      'seconds' % {'zone': zone,
                                   'period': str(self.delay - period)})

            # Don't grant the lock for the zone
            return False

    def release(self, zone):
        # Release the lock
        with self.lock:
            try:
                self.data.pop(zone)
            except KeyError:
                pass


class LimitNotifyMiddleware(DNSMiddleware):
    """Middleware that rate limits NOTIFYs to the Agent"""

    def __init__(self, application):
        super(LimitNotifyMiddleware, self).__init__(application)

        self.delay = cfg.CONF['service:agent'].notify_delay
        self.locker = ZoneLock(self.delay)

    def process_request(self, request):
        opcode = request.opcode()
        if opcode != dns.opcode.NOTIFY:
            return None

        zone_name = request.question[0].name.to_text().decode('utf-8')

        if self.locker.acquire(zone_name):
            time.sleep(self.delay)
            self.locker.release(zone_name)
            return None
        else:
            LOG.debug('Threw away NOTIFY for %(zone)s, already '
                     'working on an update.' % {'zone': zone_name})
            response = dns.message.make_response(request)
            # Provide an authoritative answer
            response.flags |= dns.flags.AA
            return (response,)


def from_dnspython_zone(dnspython_zone):
    # dnspython never builds a zone with more than one SOA, even if we give
    # it a zonefile that contains more than one
    soa = dnspython_zone.get_rdataset(dnspython_zone.origin, 'SOA')
    if soa is None:
        raise exceptions.BadRequest('An SOA record is required')
    if soa.ttl == 0:
        soa.ttl = cfg.CONF['service:central'].min_ttl
    email = soa[0].rname.to_text(omit_final_dot=True).decode('utf-8')
    email = email.replace('.', '@', 1)
    values = {
        'name': dnspython_zone.origin.to_text().decode('utf-8'),
        'email': email,
        'ttl': soa.ttl,
        'serial': soa[0].serial,
        'retry': soa[0].retry,
        'expire': soa[0].expire
    }

    zone = objects.Zone(**values)

    rrsets = dnspyrecords_to_recordsetlist(dnspython_zone.nodes)
    zone.recordsets = rrsets
    return zone


def dnspyrecords_to_recordsetlist(dnspython_records):
    rrsets = objects.RecordSetList()

    for rname in six.iterkeys(dnspython_records):
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
        'name': rname.to_text().decode('utf-8'),
        'type': record_type
    }

    if rdataset.ttl != 0:
        values['ttl'] = rdataset.ttl

    rrset = objects.RecordSet(**values)
    rrset.records = objects.RecordList()

    for rdata in rdataset:
        rr = objects.Record(data=rdata.to_text())
        rrset.records.append(rr)
    return rrset


def do_axfr(zone_name, servers, timeout=None, source=None):
    """
    Requests an AXFR for a given zone name and process the response

    :returns: Zone instance from dnspython
    """
    random.shuffle(servers)
    timeout = timeout or cfg.CONF["service:mdns"].xfr_timeout

    xfr = None

    for srv in servers:
        to = eventlet.Timeout(timeout)
        log_info = {'name': zone_name, 'host': srv}
        try:
            LOG.info(_LI("Doing AXFR for %(name)s from %(host)s"), log_info)

            xfr = dns.query.xfr(srv['host'], zone_name, relativize=False,
                                timeout=1, port=srv['port'], source=source)
            raw_zone = dns.zone.from_xfr(xfr, relativize=False)
            break
        except eventlet.Timeout as t:
            if t == to:
                msg = _LE("AXFR timed out for %(name)s from %(host)s")
                LOG.error(msg % log_info)
                continue
        except dns.exception.FormError:
            msg = _LE("Zone %(name)s is not present on %(host)s."
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
            to.cancel()
        continue
    else:
        msg = _LE("XFR failed for %(name)s. No servers in %(servers)s was "
                  "reached.")
        raise exceptions.XFRFailure(
            msg % {"name": zone_name, "servers": servers})

    LOG.debug("AXFR Successful for %s" % raw_zone.origin.to_text())

    return raw_zone
