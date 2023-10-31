# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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

from designate.context import DesignateContext
from designate.notification_handler.base import NotificationHandler


LOG = logging.getLogger(__name__)

# Setup a config group
cfg.CONF.register_group(cfg.OptGroup(
    name='handler:sample',
    title="Configuration for Sample Notification Handler"
))

# Setup the config options
cfg.CONF.register_opts([
    cfg.StrOpt('control-exchange', default='nova'),
    cfg.ListOpt('notification-topics', default=['designate']),
    cfg.StrOpt('zone-name', default='example.org.'),
    cfg.StrOpt('zone-id', default='12345'),
], group='handler:sample')


class SampleHandler(NotificationHandler):
    """Sample Handler"""
    __plugin_name__ = 'sample'

    def get_exchange_topics(self):
        """
        Return a tuple of (exchange, [topics]) this handler wants to receive
        events from.
        """
        exchange = cfg.CONF[self.name].control_exchange
        topics = [topic for topic in cfg.CONF[self.name].notification_topics]
        return exchange, topics

    def get_event_types(self):
        return [
            'compute.instance.create.end'
        ]

    def process_notification(self, context, event_type, payload):
        # Do something with the notification.. e.g:
        zone_id = cfg.CONF[self.name].zone_id
        zone_name = cfg.CONF[self.name].zone_name

        record_name = '{}.{}'.format(payload['instance_id'], zone_name)

        context = DesignateContext().elevated()
        context.all_tenants = True
        # context.edit_managed_records = True

        for fixed_ip in payload['fixed_ips']:
            recordset_values = {
                'zone_id': zone_id,
                'name': record_name,
                'type': 'A' if fixed_ip['version'] == 4 else 'AAAA'
            }

            record_values = {
                'data': fixed_ip['address'],
            }

            self.central_api.create_managed_records(
                context, zone_id,
                records_values=[record_values],
                recordset_values=recordset_values,
            )
