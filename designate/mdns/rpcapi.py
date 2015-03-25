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
from oslo.config import cfg
from oslo_log import log as logging
from oslo import messaging

from designate.i18n import _LI
from designate import rpc


LOG = logging.getLogger(__name__)

MDNS_API = None


class MdnsAPI(object):

    """
    Client side of the mdns RPC API.

    Notify API version history:

        1.0 - Added notify_zone_changed and poll_for_serial_number.
        1.1 - Added get_serial_number.

    XFR API version history:
        1.0 - Added perform_zone_xfr.
    """
    RPC_NOTIFY_API_VERSION = '1.1'
    RPC_XFR_API_VERSION = '1.0'

    def __init__(self, topic=None):
        topic = topic if topic else cfg.CONF.mdns_topic

        notify_target = messaging.Target(topic=topic,
                                         namespace='notify',
                                         version=self.RPC_NOTIFY_API_VERSION)
        self.notify_client = rpc.get_client(notify_target, version_cap='1.1')

        xfr_target = messaging.Target(topic=topic,
                                      namespace='xfr',
                                      version=self.RPC_XFR_API_VERSION)
        self.xfr_client = rpc.get_client(xfr_target, version_cap='1.0')

    @classmethod
    def get_instance(cls):
        """
        The rpc.get_client() which is called upon the API object initialization
        will cause a assertion error if the designate.rpc.TRANSPORT isn't setup
        by rpc.init() before.

        This fixes that by creating the rpcapi when demanded.
        """
        global MDNS_API
        if not MDNS_API:
            MDNS_API = cls()
        return MDNS_API

    def notify_zone_changed(self, context, domain, nameserver, timeout,
                            retry_interval, max_retries, delay):
        LOG.info(_LI("notify_zone_changed: Calling mdns for zone '%(zone)s', "
                     "serial '%(serial)s' to nameserver '%(host)s:%(port)s'") %
                 {'zone': domain.name, 'serial': domain.serial,
                  'host': nameserver.host, 'port': nameserver.port})
        # The notify_zone_changed method is a cast rather than a call since the
        # caller need not wait for the notify to complete.
        return self.notify_client.cast(
            context, 'notify_zone_changed', domain=domain,
            nameserver=nameserver, timeout=timeout,
            retry_interval=retry_interval, max_retries=max_retries,
            delay=delay)

    def poll_for_serial_number(self, context, domain, nameserver, timeout,
                               retry_interval, max_retries, delay):
        LOG.info(
            _LI("poll_for_serial_number: Calling mdns for zone '%(zone)s', "
                "serial '%(serial)s' on nameserver '%(host)s:%(port)s'") %
            {'zone': domain.name, 'serial': domain.serial,
             'host': nameserver.host, 'port': nameserver.port})
        # The poll_for_serial_number method is a cast rather than a call since
        # the caller need not wait for the poll to complete. Mdns informs pool
        # manager of the return value using update_status
        return self.notify_client.cast(
            context, 'poll_for_serial_number', domain=domain,
            nameserver=nameserver, timeout=timeout,
            retry_interval=retry_interval, max_retries=max_retries,
            delay=delay)

    def get_serial_number(self, context, domain, nameserver, timeout,
                          retry_interval, max_retries, delay):
        LOG.info(
            _LI("get_serial_number: Calling mdns for zone '%(zone)s', serial "
                "%(serial)s' on nameserver '%(host)s:%(port)s'") %
            {'zone': domain.name, 'serial': domain.serial,
             'host': nameserver.host, 'port': nameserver.port})
        cctxt = self.notify_client.prepare(version='1.1')
        return cctxt.call(
            context, 'get_serial_number', domain=domain,
            nameserver=nameserver, timeout=timeout,
            retry_interval=retry_interval, max_retries=max_retries,
            delay=delay)

    def perform_zone_xfr(self, context, domain):
        LOG.info(_LI("perform_zone_xfr: Calling mdns for zone %(zone)s") %
                 {"zone": domain.name})
        return self.xfr_client.cast(context, 'perform_zone_xfr', domain=domain)
