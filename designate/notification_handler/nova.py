# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from oslo_config import cfg
from oslo_log import log as logging

from designate.notification_handler.base import BaseAddressHandler


LOG = logging.getLogger(__name__)

# TODO(trungnv): update default format for v4 and v6 in these cfg.
nova_group = cfg.OptGroup(
    name='handler:nova_fixed',
    title="Configuration for Nova Notification Handler"
)

nova_opts = [
    cfg.ListOpt('notification-topics', default=['notifications'],
                help='notification any events from nova'),
    cfg.StrOpt('control-exchange', default='nova',
               help='control-exchange for nova notification'),
    cfg.StrOpt('zone-id', help='Zone ID with each notification'),
    cfg.MultiStrOpt('formatv4', help='IPv4 format'),
    cfg.MultiStrOpt('format', deprecated_for_removal=True,
                    deprecated_reason="Replaced by 'formatv4/formatv6'",
                    help='format which replaced by formatv4/formatv6'),
    cfg.MultiStrOpt('formatv6', help='IPv6 format')
]

cfg.CONF.register_group(nova_group)
cfg.CONF.register_opts(nova_opts, group=nova_group)


class NovaFixedHandler(BaseAddressHandler):
    """Handler for Nova's notifications"""
    __plugin_name__ = 'nova_fixed'

    def get_exchange_topics(self):
        exchange = cfg.CONF[self.name].control_exchange

        topics = [topic for topic in cfg.CONF[self.name].notification_topics]

        return (exchange, topics)

    def get_event_types(self):
        return [
            'compute.instance.create.end',
            'compute.instance.delete.start',
        ]

    def _get_ip_data(self, addr_dict):
        data = super(NovaFixedHandler, self)._get_ip_data(addr_dict)
        data['label'] = addr_dict['label']
        return data

    def process_notification(self, context, event_type, payload):
        LOG.debug('NovaFixedHandler received notification - %s', event_type)

        zone_id = cfg.CONF[self.name].zone_id
        if event_type == 'compute.instance.create.end':
            payload['project'] = context.get("project_name", None)
            self._create(addresses=payload['fixed_ips'],
                         extra=payload,
                         zone_id=zone_id,
                         resource_id=payload['instance_id'],
                         resource_type='instance')

        elif event_type == 'compute.instance.delete.start':
            self._delete(zone_id=zone_id,
                         resource_id=payload['instance_id'],
                         resource_type='instance')
