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
from oslo_log import log as logging

import designate.conf
from designate.notification_handler import base


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class FakeHandler(base.NotificationHandler):
    __plugin_name__ = 'fake'

    def get_exchange_topics(self):
        exchange = CONF[self.name].control_exchange
        topics = CONF[self.name].notification_topics
        return exchange, topics

    def get_event_types(self):
        return CONF[self.name].allowed_event_types

    def process_notification(self, context, event_type, payload):
        LOG.info('%s: received notification - %s', self.name, event_type)
