# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import dns
from oslo import messaging
from oslo.config import cfg

from designate import exceptions
from designate.openstack.common import log as logging
from designate.i18n import _LI
from designate.i18n import _LW

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class NotifyEndpoint(object):
    RPC_NOTIFY_API_VERSION = '0.1'

    target = messaging.Target(
        namespace='notify', version=RPC_NOTIFY_API_VERSION)

    def __init__(self, *args, **kwargs):
        # Parse the slave-nameserver-ips-and-ports.
        self._slave_server_ips = []
        self._slave_server_ports = []
        self._total_slave_nameservers = 0
        for slave in CONF['service:mdns'].slave_nameserver_ips_and_ports:
            slave_details = slave.split(':')

            # Check each entry to ensure that it has an IP and port.
            if (len(slave_details) != 2):
                raise exceptions.ConfigurationError(
                    "'slave-nameserver-ips-and-ports' in ['service:mdns'] is "
                    "not in the correct format. Expected format 'ipaddress:"
                    "port'. Got %(list_item)s" % {'list_item': slave})

            self._slave_server_ips.append(slave_details[0])
            self._slave_server_ports.append(int(slave_details[1]))
            self._total_slave_nameservers += 1

        LOG.info(_LI("slave nameserver ips = %(slave_server_ips)s") %
                 {"slave_server_ips": self._slave_server_ips})
        LOG.info(_LI("slave nameserver ports = %(slave_server_ports)s") %
                 {"slave_server_ports": self._slave_server_ports})
        LOG.info(_LI("started mdns notify endpoint"))

    def notify_zone_changed(self, context, zone_name):
        """
        :param context: The user context.
        :param zone_name: The zone name for which some data changed.
        :return: None
        """
        notify_message = self._get_notify_message(context, zone_name)
        for current in range(0, self._total_slave_nameservers):
            retry = -1

            # retry sending NOTIFY if specified by configuration file.
            while retry < CONF['service:mdns'].notify_retries:
                retry = retry + 1
                response = self._send_notify_message(
                    context, zone_name, notify_message,
                    self._slave_server_ips[current],
                    self._slave_server_ports[current],
                    timeout=CONF['service:mdns'].notify_timeout)
                if isinstance(response, dns.exception.Timeout):
                    # retry sending the message if we get a Timeout.
                    continue
                else:
                    break

    def _get_notify_message(self, context, zone_name):
        """
        :param context: The user context.
        :param zone_name: The zone name for which a NOTIFY needs to be sent.
        :return: The constructed notify message.
        """
        notify_message = dns.message.make_query(zone_name, dns.rdatatype.SOA)
        notify_message.flags = 0
        notify_message.set_opcode(dns.opcode.NOTIFY)
        notify_message.set_rcode(dns.rcode.NOERROR)
        notify_message.flags = notify_message.flags | dns.flags.AA

        return notify_message

    def _send_notify_message(self, context, zone_name, notify_message, dest_ip,
                             dest_port, timeout):
        """
        :param context: The user context.
        :param zone_name: The zone name for which a NOTIFY needs to be sent.
        :param notify_message: The notify message that needs to be sent to the
        slave name servers.
        :param dest_ip: The destination ip.
        :param dest_port: The destination port.
        :param timeout: The timeout in seconds to wait for a response.
        :return: None
        """
        try:
            response = dns.query.udp(
                notify_message, dest_ip, port=dest_port, timeout=timeout)

            # Check that we actually got a NOERROR in the rcode
            if dns.rcode.from_flags(
                    response.flags, response.ednsflags) != dns.rcode.NOERROR:
                LOG.warn(_LW("Failed to get NOERROR while trying to notify "
                             "change in %(zone)s to %(server)s:%(port)d. "
                             "Response message = %(resp)s") %
                         {'zone': zone_name, 'server': dest_ip,
                          'port': dest_port, 'resp': str(response)})
            return response
        except dns.exception.Timeout as timeout:
            LOG.warn(_LW("Got Timeout while trying to notify change in"
                         " %(zone)s to %(server)s:%(port)d. ") %
                     {'zone': zone_name, 'server': dest_ip, 'port': dest_port})
            return timeout
        except dns.query.BadResponse as badResponse:
            LOG.warn(_LW("Got BadResponse while trying to notify "
                         "change in %(zone)s to %(server)s:%(port)d") %
                     {'zone': zone_name, 'server': dest_ip, 'port': dest_port})
            return badResponse
