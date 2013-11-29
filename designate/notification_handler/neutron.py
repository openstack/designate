# Copyright 2012 Bouvet ASA
#
# Author: Endre Karlson <endre.karlson@bouvet.no>
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
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.notification_handler.base import BaseAddressHandler

LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='handler:neutron_floatingip',
    title="Configuration for Neutron Notification Handler"
))

cfg.CONF.register_opts([
    cfg.ListOpt('notification-topics', default=['monitor']),
    cfg.StrOpt('control-exchange', default='neutron'),
    cfg.StrOpt('domain-id', default=None),
    cfg.StrOpt('format', default=None)
], group='handler:neutron_floatingip')


class NeutronFloatingHandler(BaseAddressHandler):
    """ Handler for Neutron's notifications """
    __plugin_name__ = 'neutron_floatingip'

    def get_exchange_topics(self):
        exchange = cfg.CONF[self.name].control_exchange

        topics = [topic + ".info"
                  for topic in cfg.CONF[self.name].notification_topics]

        return (exchange, topics)

    def get_event_types(self):
        return [
            'floatingip.update.end',
        ]

    def process_notification(self, event_type, payload):
        LOG.debug('%s recieved notification - %s',
                  self.get_canonical_name(), event_type)

        # FIXME: Neutron doesn't send ipv in the payload, should maybe
        # determine this?
        if event_type not in self.get_event_types():
            raise ValueError('NovaFixedHandler recieved an invalid event type')

        floating = payload['floatingip']

        if floating['fixed_ip_address']:
            address = {
                'version': 4,
                'address': floating['floating_ip_address']}
            self._create([address], payload, resource_id=floating['id'],
                         resource_type='floatingip')
        elif not floating['fixed_ip_address']:
            self._delete(resource_id=payload['floatingip']['id'],
                         resource_type='floatingip')
