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

from designate.objects import Record
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
    cfg.StrOpt('domain-name', default='example.org.'),
    cfg.StrOpt('domain-id', default='12345'),
], group='handler:sample')


class SampleHandler(NotificationHandler):
    """Sample Handler"""
    __plugin_name__ = 'sample'

    def get_exchange_topics(self):
        """
        Return a tuple of (exchange, [topics]) this handler wants to receive
        events from.
        """
        exchange = cfg.CONF['handler:sample'].control_exchange

        notification_topics = cfg.CONF['handler:sample'].notification_topics
        notification_topics = [t + ".info" for t in notification_topics]

        return (exchange, notification_topics)

    def get_event_types(self):
        return [
            'compute.instance.create.end'
        ]

    def process_notification(self, context, event_type, payload):
        # Do something with the notification.. e.g:
        domain_id = cfg.CONF['handler:sample'].domain_id
        domain_name = cfg.CONF['handler:sample'].domain_name

        hostname = '%s.%s' % (payload['instance_id'], domain_name)

        for fixed_ip in payload['fixed_ips']:
            if fixed_ip['version'] == 4:
                values = dict(
                    type='A',
                    name=hostname,
                    data=fixed_ip['address']
                )
                self.central_api.create_record(domain_id, Record(**values))

            elif fixed_ip['version'] == 6:
                values = dict(
                    type='AAAA',
                    name=hostname,
                    data=fixed_ip['address']
                )
                self.central_api.create_record(domain_id, Record(**values))
