# Copyright 2016 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace>
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
# under the License.mport threading
import dns
import dns.exception
import dns.query
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def prepare_msg(zone_name, rdatatype=dns.rdatatype.SOA, notify=False):
    """
    Do the needful to set up a dns packet with dnspython
    """
    dns_message = dns.message.make_query(zone_name, rdatatype)
    if notify:
        dns_message.set_opcode(dns.opcode.NOTIFY)
    else:
        dns_message.set_opcode(dns.opcode.QUERY)
    return dns_message


def dig(zone_name, host, rdatatype, port=53):
    """
    Set up and send a regular dns query, datatype configurable
    """
    query = prepare_msg(zone_name, rdatatype=rdatatype)

    return send_dns_msg(query, host, port=port)


def notify(zone_name, host, port=53):
    """
    Set up a notify packet and send it
    """
    msg = prepare_msg(zone_name, notify=True)

    return send_dns_msg(msg, host, port=port)


def send_dns_msg(dns_message, host, port=53):
    """
    Send the dns message and return the response

    :return: dns.Message of the response to the dns query
    """
    # This can raise some exceptions, but we'll catch them elsewhere
    if not CONF['service:mdns'].all_tcp:
        return dns.query.udp(
            dns_message, host, port=port, timeout=10)
    else:
        return dns.query.tcp(
            dns_message, host, port=port, timeout=10)


def get_serial(zone_name, host, port=53):
    """
    Possibly raises dns.exception.Timeout or dns.query.BadResponse.
    Possibly returns 0 if, e.g., the answer section is empty.
    """
    resp = dig(zone_name, host, dns.rdatatype.SOA, port=port)
    if not resp.answer:
        return 0
    rdataset = resp.answer[0].to_rdataset()
    if not rdataset:
        return 0
    return rdataset[0].serial
