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
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.notification_handler.base import BaseAddressHandler

LOG = logging.getLogger(__name__)


class NovaFixedHandler(BaseAddressHandler):
    __plugin_name__ = 'nova_fixed'
    """ Handler for Nova's notifications """

    @classmethod
    def get_opts(cls):
        opts = super(NovaFixedHandler, cls).get_opts()
        opts.extend([
            cfg.ListOpt('notification-topics', default=['monitor']),
            cfg.StrOpt('control-exchange', default='nova')])
        return opts

    def get_exchange_topics(self):
        exchange = self.config.control_exchange

        topics = [topic + ".info"
                  for topic in self.config.notification_topics]

        return (exchange, topics)

    def get_event_types(self):
        return [
            'compute.instance.create.end',
            'compute.instance.delete.start',
        ]

    def process_notification(self, event_type, payload):
        LOG.debug('NovaFixedHandler recieved notification - %s' % event_type)

        if event_type == 'compute.instance.create.end':
            self._create(payload['fixed_ips'], payload,
                         resource_id=payload['instance_id'],
                         resource_type='instance')

        elif event_type == 'compute.instance.delete.start':
            self._delete(resource_id=payload['instance_id'],
                         resource_type='instance')
        else:
            raise ValueError('NovaFixedHandler recieved an invalid event type')
