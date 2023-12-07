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

import dns.exception
import dns.message
import dns.opcode
import dns.query
import dns.rdatatype
import dns.zone
import eventlet
from oslo_log import log as logging
from oslo_serialization import base64

import designate.conf
from designate import context
from designate import exceptions
from designate import objects

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class TsigKeyring(dict):
    """Implements the DNSPython KeyRing API, backed by the Designate DB"""

    def __init__(self, storage):
        super().__init__()
        self.storage = storage

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, default=None):
        try:
            name = key.to_text(True)
            criterion = {'name': name}
            tsigkey = self.storage.find_tsigkey(
                context.get_current(), criterion
            )

            return base64.decode_as_bytes(tsigkey.secret)

        except exceptions.TsigKeyNotFound:
            return default


def from_dnspython_zone(dnspython_zone):
    # dnspython never builds a zone with more than one SOA, even if we give
    # it a zonefile that contains more than one
    soa = dnspython_zone.get_rdataset(dnspython_zone.origin, 'SOA')
    if soa is None:
        raise exceptions.BadRequest('An SOA record is required')
    if soa.ttl == 0:
        soa.ttl = CONF['service:central'].min_ttl
    email = soa[0].rname.to_text(omit_final_dot=True)
    email = email.replace('.', '@', 1)

    name = dnspython_zone.origin.to_text()
    values = {
        'name': name,
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
    for rname in dnspython_records.keys():
        for rdataset in dnspython_records[rname]:
            rrsets.append(dnspythonrecord_to_recordset(rname, rdataset))
    return rrsets


def dnspythonrecord_to_recordset(rname, rdataset):
    record_type = dns.rdatatype.to_text(rdataset.rdtype)

    name = rname.to_text()

    # Create the other recordsets

    values = {
        'name': name,
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


def xfr_timeout():
    return CONF['service:worker'].xfr_timeout


def do_axfr(zone_name, servers, source=None):
    """
    Requests an AXFR for a given zone name and process the response

    :returns: Zone instance from dnspython
    """
    random.shuffle(servers)

    xfr = None
    for srv in servers:
        for address in get_ip_addresses(srv['host']):
            to = eventlet.Timeout(xfr_timeout())
            log_info = {'name': zone_name, 'host': srv, 'address': address}
            try:
                LOG.info(
                    'Doing AXFR for %(name)s from %(host)s %(address)s',
                    log_info
                )
                xfr = dns.query.xfr(
                    address, zone_name, relativize=False, timeout=1,
                    port=srv['port'], source=source
                )
                raw_zone = dns.zone.from_xfr(xfr, relativize=False)
                LOG.debug('AXFR Successful for %s', raw_zone.origin.to_text())
                return raw_zone
            except eventlet.Timeout as t:
                if t == to:
                    LOG.error('AXFR timed out for %(name)s from %(host)s',
                              log_info)
                    continue
            except dns.exception.FormError:
                LOG.error('Zone %(name)s is not present on %(host)s.'
                          'Trying next server.', log_info)
            except OSError:
                LOG.error('Connection error when doing AXFR for %(name)s from '
                          '%(host)s', log_info)
            except Exception:
                LOG.exception('Problem doing AXFR %(name)s from %(host)s. '
                              'Trying next server.', log_info)
            finally:
                to.cancel()

    raise exceptions.XFRFailure(
        'XFR failed for %(name)s. No servers in %(servers)s was reached.' %
        {'name': zone_name, 'servers': servers}
    )


def prepare_dns_message(zone_name, rdatatype, opcode):
    """
    Create a dns message using dnspython
    """
    dns_message = dns.message.make_query(zone_name, rdatatype)
    dns_message.set_opcode(opcode)
    return dns_message


def notify(zone_name, host, port=53, timeout=10):
    """
    Create a NOTIFY message and send it
    """
    dns_message = prepare_dns_message(
        zone_name, rdatatype=dns.rdatatype.SOA, opcode=dns.opcode.NOTIFY
    )
    return send_dns_message(dns_message, host, port=port, timeout=timeout)


def soa_query(zone_name, host, port=53, timeout=10):
    """
    Create a SOA Query message and send it
    """
    dns_message = prepare_dns_message(
        zone_name, rdatatype=dns.rdatatype.SOA, opcode=dns.opcode.QUERY
    )
    return send_dns_message(dns_message, host, port=port, timeout=timeout)


def use_all_tcp():
    return CONF['service:worker'].all_tcp


def send_dns_message(dns_message, host, port=53, timeout=10):
    """
    Send the dns message and return the response

    :return: dns.Message of the response to the dns query
    """
    ip_address = get_ip_address(host)
    # This can raise some exceptions, but we'll catch them elsewhere
    if not use_all_tcp():
        return dns.query.udp(
            dns_message, ip_address, port=port, timeout=timeout)
    return dns.query.tcp(
        dns_message, ip_address, port=port, timeout=timeout)


def get_serial(zone_name, host, port=53):
    """
    Possibly raises dns.exception.Timeout or dns.query.BadResponse.
    Possibly returns 0 if, e.g., the answer section is empty.
    """
    resp = soa_query(zone_name, host, port=port)
    if not resp.answer:
        return 0
    rdataset = resp.answer[0].to_rdataset()
    if not rdataset:
        return 0
    return rdataset[0].serial


def get_ip_address(ip_address_or_hostname):
    """
    Provide an ip or hostname and return a valid ip4 or ipv6 address.

    :return: ip address
    """
    addresses = get_ip_addresses(ip_address_or_hostname)
    if not addresses:
        return None
    return addresses[0]


def get_ip_addresses(ip_address_or_hostname):
    """
    Provide an ip or hostname and return all valid ip4 or ipv6 addresses.

    :return: ip addresses
    """
    addresses = []
    for res in socket.getaddrinfo(ip_address_or_hostname, 0):
        addresses.append(res[4][0])
    return list(set(addresses))
