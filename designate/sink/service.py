# Copyright 2012 Managed I.T.
# Copyright 2014 Hewlett-Packard Development Company, L.P.
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


from oslo_log import log as logging
import oslo_messaging as messaging

import designate.conf
from designate import notification_handler
from designate import rpc
from designate import service


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class Service(service.Service):
    def __init__(self):
        super().__init__(
            self.service_name, threads=CONF['service:sink'].threads
        )

        # Initialize extensions
        self._notification_listener = None
        self.handlers = self.init_extensions()
        self.allowed_event_types = self.get_allowed_event_types(self.handlers)

    @property
    def service_name(self):
        return 'sink'

    @staticmethod
    def init_extensions():
        """Loads and prepares all enabled extensions"""
        notification_handlers = notification_handler.get_notification_handlers(
            CONF['service:sink'].enabled_notification_handlers
        )

        if not notification_handlers:
            LOG.warning('No designate-sink handlers enabled or loaded')

        return notification_handlers

    @staticmethod
    def get_allowed_event_types(handlers):
        """Build a list of all allowed event types."""
        allowed_event_types = []

        for handler in handlers:
            for event_type in handler.get_event_types():
                if event_type in allowed_event_types:
                    continue
                allowed_event_types.append(event_type)

        return allowed_event_types

    def start(self):
        super().start()

        # Setup notification subscriptions and start consuming
        targets = self._get_targets()

        # TODO(ekarlso): Change this is to endpoint objects rather then
        # ourselves?
        if targets:
            self._notification_listener = rpc.get_notification_listener(
                targets, [self],
                pool=CONF['service:sink'].listener_pool_name
            )
            self._notification_listener.start()

    def stop(self, graceful=True):
        if self._notification_listener:
            self._notification_listener.stop()
        super().stop(graceful)

    def _get_targets(self):
        """
        Set's up subscriptions for the various exchange+topic combinations that
        we have a handler for.
        """
        targets = []
        for handler in self.handlers:
            exchange, topics = handler.get_exchange_topics()

            for topic in topics:
                target = messaging.Target(exchange=exchange, topic=topic)
                targets.append(target)
        return targets

    def info(self, context, publisher_id, event_type, payload, metadata):
        """
        Processes an incoming notification, offering each extension the
        opportunity to handle it.
        """
        if event_type not in self.allowed_event_types:
            return

        for handler in self.handlers:
            if event_type in handler.get_event_types():
                LOG.debug('Found handler for: %s', event_type)
                handler.process_notification(context, event_type, payload)
