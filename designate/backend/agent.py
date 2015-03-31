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
import eventlet
import dns
import dns.rdataclass
import dns.rdatatype
import dns.exception
import dns.flags
import dns.rcode
import dns.message
import dns.opcode
from oslo.config import cfg
from oslo_log import log as logging

from designate.i18n import _LI
from designate.i18n import _LW
from designate.backend import base
from designate import exceptions

dns_query = eventlet.import_patched('dns.query')

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class AgentPoolBackend(base.Backend):
    __plugin_name__ = 'agent'

    def __init__(self, target):
        super(AgentPoolBackend, self).__init__(target)
        self.host = self.options.get('host')
        self.port = int(self.options.get('port'))

    def create_domain(self, context, domain):
        LOG.debug('Create Domain')
        response, retry = self._make_and_send_dns_message(domain.name, 15, 14,
                          65282, 65280, self.host, self.port)
        if response is None:
            raise exceptions.Backend()

    def delete_domain(self, context, domain):
        LOG.debug('Delete Domain')
        response, retry = self._make_and_send_dns_message(domain.name, 15, 14,
                          65283, 65280, self.host, self.port)
        if response is None:
            raise exceptions.Backend()

    def _make_and_send_dns_message(self, domain_name, timeout, opcode,
                                  rdatatype, rdclass, dest_ip,
                                  dest_port):
        dns_message = self._make_dns_message(domain_name, opcode, rdatatype,
                                             rdclass)

        retry = 0
        response = None

        LOG.info(_LI("Sending '%(msg)s' for '%(zone)s' to '%(server)s:"
                     "%(port)d'.") %
                 {'msg': str(opcode),
                  'zone': domain_name, 'server': dest_ip,
                  'port': dest_port})
        response = self._send_dns_message(
            dns_message, dest_ip, dest_port, timeout)

        if isinstance(response, dns.exception.Timeout):
            LOG.warn(_LW("Got Timeout while trying to send '%(msg)s' for "
                         "'%(zone)s' to '%(server)s:%(port)d'. Timeout="
                         "'%(timeout)d' seconds. Retry='%(retry)d'") %
                     {'msg': str(opcode),
                      'zone': domain_name, 'server': dest_ip,
                      'port': dest_port, 'timeout': timeout,
                      'retry': retry})
            response = None
        elif isinstance(response, dns_query.BadResponse):
            LOG.warn(_LW("Got BadResponse while trying to send '%(msg)s' "
                         "for '%(zone)s' to '%(server)s:%(port)d'. Timeout"
                         "='%(timeout)d' seconds. Retry='%(retry)d'") %
                     {'msg': str(opcode),
                      'zone': domain_name, 'server': dest_ip,
                      'port': dest_port, 'timeout': timeout,
                      'retry': retry})
            response = None
            return (response, retry)
        # Check that we actually got a NOERROR in the rcode and and an
        # authoritative answer
        elif not (response.flags & dns.flags.AA) or dns.rcode.from_flags(
                response.flags, response.ednsflags) != dns.rcode.NOERROR:
            LOG.warn(_LW("Failed to get expected response while trying to "
                         "send '%(msg)s' for '%(zone)s' to '%(server)s:"
                         "%(port)d'. Response message: %(resp)s") %
                     {'msg': str(opcode),
                      'zone': domain_name, 'server': dest_ip,
                      'port': dest_port, 'resp': str(response)})
            response = None
            return (response, retry)
        else:
            return (response, retry)

        return (response, retry)

    def _make_dns_message(self, zone_name, opcode, rdatatype, rdclass):
        dns_message = dns.message.make_query(zone_name, rdatatype,
                                             rdclass=rdclass)
        dns_message.flags = 0

        dns_message.set_opcode(opcode)
        dns_message.flags |= dns.flags.AA

        return dns_message

    def _send_dns_message(self, dns_message, dest_ip, dest_port, timeout):
        try:
            if not CONF['service:mdns'].all_tcp:
                response = dns_query.udp(
                    dns_message, dest_ip, port=dest_port, timeout=timeout)
            else:
                response = dns_query.tcp(
                    dns_message, dest_ip, port=dest_port, timeout=timeout)
            return response
        except dns.exception.Timeout as timeout:
            return timeout
        except dns_query.BadResponse as badResponse:
            return badResponse
