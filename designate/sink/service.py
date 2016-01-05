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
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from designate.i18n import _LW
from designate import notification_handler
from designate import rpc
from designate import service


LOG = logging.getLogger(__name__)


class Service(service.Service):
    def __init__(self, threads=None):
        super(Service, self).__init__(threads=threads)

        # Initialize extensions
        self.handlers = self._init_extensions()
        self.subscribers = self._get_subscribers()

    @property
    def service_name(self):
        return 'sink'

    def _init_extensions(self):
        """Loads and prepares all enabled extensions"""

        enabled_notification_handlers = \
            cfg.CONF['service:sink'].enabled_notification_handlers

        notification_handlers = notification_handler.get_notification_handlers(
            enabled_notification_handlers)

        if len(notification_handlers) == 0:
            LOG.warning(_LW('No designate-sink handlers enabled or loaded'))

        return notification_handlers

    def _get_subscribers(self):
        subscriptions = {}
        for handler in self.handlers:
            for et in handler.get_event_types():
                subscriptions.setdefault(et, [])
                subscriptions[et].append(handler)
        return subscriptions

    def start(self):
        super(Service, self).start()

        # Setup notification subscriptions and start consuming
        targets = self._get_targets()

        # TODO(ekarlso): Change this is to endpoint objects rather then
        # ourselves?
        self._server = rpc.get_listener(targets, [self])

        if len(targets) > 0:
            self._server.start()

    def stop(self):
        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self._server.stop()
        except Exception:
            pass

        super(Service, self).stop()

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

    def _get_handler_event_types(self):
        """return a dict - keys are the event types we can handle"""
        return self.subscribers

    def info(self, context, publisher_id, event_type, payload, metadata):
        """
        Processes an incoming notification, offering each extension the
        opportunity to handle it.
        """
        # NOTE(zykes): Only bother to actually do processing if there's any
        # matching events, skips logging of things like compute.exists etc.
        if event_type in self._get_handler_event_types():
            for handler in self.handlers:
                if event_type in handler.get_event_types():
                    LOG.debug('Found handler for: %s' % event_type)
                    handler.process_notification(context, event_type, payload)
