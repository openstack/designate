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

"""
    backend.agent
    ~~~~~~~~~~~~~
    Agent backend for Pool Manager.
    Sends DNS requests to a remote agent using private OPCODEs to trigger
    creation / deletion / update of zones.

    Configured in the [service:pool_manager] section
"""

import dns
import dns.exception
import dns.flags
import dns.message
import dns.opcode
import dns.rcode
import dns.rdataclass
import dns.rdatatype
from oslo_config import cfg
from oslo_log import log as logging

from designate.backend import base
from designate.backend import private_codes
from designate.conf.agent import DEFAULT_AGENT_PORT
from designate import dnsutils
from designate import exceptions


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class AgentPoolBackend(base.Backend):
    __plugin_name__ = 'agent'
    __backend_status__ = 'untested'

    def __init__(self, target):
        super(AgentPoolBackend, self).__init__(target)
        self.host = self.options.get('host', '127.0.0.1')
        self.port = int(self.options.get('port', DEFAULT_AGENT_PORT))
        self.timeout = CONF['service:worker'].poll_timeout
        self.retry_interval = CONF['service:worker'].poll_retry_interval
        self.max_retries = CONF['service:worker'].poll_max_retries
        # FIXME: the agent retries creating zones without any interval

        # TODO(johnsom) Remove this after the agents framework is removed or
        # the protocol has been updated to not use an unassigned opcode(14).
        dns.opcode.Opcode = private_codes.OpcodeWith14

    def create_zone(self, context, zone):
        LOG.debug('Create Zone')
        response = self._make_and_send_dns_message(
            zone.name,
            self.timeout,
            private_codes.CC,
            private_codes.CREATE,
            private_codes.CLASSCC,
            self.host,
            self.port
        )
        if response is None:
            raise exceptions.Backend('Failed create_zone()')

    def update_zone(self, context, zone):
        LOG.debug('Update Zone')

    def delete_zone(self, context, zone):
        LOG.debug('Delete Zone')
        response = self._make_and_send_dns_message(
            zone.name,
            self.timeout,
            private_codes.CC,
            private_codes.DELETE,
            private_codes.CLASSCC,
            self.host,
            self.port
        )
        if response is None:
            raise exceptions.Backend('Failed delete_zone()')

    def _make_and_send_dns_message(self, zone_name, timeout, opcode,
                                   rdatatype, rdclass, dest_ip,
                                   dest_port):
        dns_message = self._make_dns_message(
            zone_name, opcode, rdatatype, rdclass
        )
        LOG.info(
            "Sending '%(msg)s' for '%(zone)s' to '%(server)s:%(port)d'.",
            {
                'msg': str(opcode),
                'zone': zone_name,
                'server': dest_ip,
                'port': dest_port
            }
        )
        try:
            response = dnsutils.send_dns_message(
                dns_message, dest_ip, port=dest_port, timeout=timeout
            )
            # Check that we actually got a NOERROR in the rcode and and an
            # authoritative answer
            if not (response.flags & dns.flags.AA) or dns.rcode.from_flags(
                    response.flags, response.ednsflags) != dns.rcode.NOERROR:
                LOG.warning(
                    "Failed to get expected response while trying to "
                    "send '%(msg)s' for '%(zone)s' to "
                    "'%(server)s:%(port)d'. Response message: %(resp)s",
                    {
                        'msg': str(opcode),
                        'zone': zone_name,
                        'server': dest_ip,
                        'port': dest_port,
                        'resp': str(response)
                    }
                )
                response = None
        except dns.exception.Timeout:
            LOG.warning(
                "Got Timeout while trying to send '%(msg)s' for "
                "'%(zone)s' to '%(server)s:%(port)d'. "
                "Timeout='%(timeout)d' seconds.",
                {
                    'msg': str(opcode),
                    'zone': zone_name,
                    'server': dest_ip,
                    'port': dest_port,
                    'timeout': timeout,
                }
            )
            response = None
        except dns.query.BadResponse:
            LOG.warning(
                "Got BadResponse while trying to send '%(msg)s' for "
                "'%(zone)s' to '%(server)s:%(port)d'. "
                "Timeout='%(timeout)d' seconds.",
                {
                    'msg': str(opcode),
                    'zone': zone_name,
                    'server': dest_ip,
                    'port': dest_port,
                    'timeout': timeout,
                }
            )
            response = None

        return response

    @staticmethod
    def _make_dns_message(zone_name, opcode, rdatatype, rdclass):
        dns_message = dns.message.make_query(zone_name, rdatatype,
                                             rdclass=rdclass)
        dns_message.flags = 0

        dns_message.set_opcode(opcode)
        dns_message.flags |= dns.flags.AA

        return dns_message
