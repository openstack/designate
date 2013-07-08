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
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.openstack.common import rpc
from designate.openstack.common import service
from stevedore.named import NamedExtensionManager
from designate import exceptions

LOG = logging.getLogger(__name__)

HANDLER_NAMESPACE = 'designate.notification.handler'


class Service(service.Service):
    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

        # Initialize extensions
        self.handlers = self._init_extensions()

        # Get a rpc connection
        self.rpc_conn = rpc.create_connection()

    def _init_extensions(self):
        """ Loads and prepares all enabled extensions """
        enabled_notification_handlers = \
            cfg.CONF['service:sink'].enabled_notification_handlers

        self.extensions_manager = NamedExtensionManager(
            HANDLER_NAMESPACE, names=enabled_notification_handlers)

        def _load_extension(ext):
            handler_cls = ext.plugin
            return handler_cls()

        try:
            return self.extensions_manager.map(_load_extension)
        except RuntimeError:
            # No handlers enabled. Bail!
            raise exceptions.ConfigurationError('No designate-sink handlers '
                                                'enabled')

    def start(self):
        super(Service, self).start()

        # Setup notification subscriptions and start consuming
        self._setup_subscriptions()
        self.rpc_conn.consume_in_thread()

    def wait(self):
        super(Service, self).wait()
        self.rpc_conn.consumer_thread.wait()

    def stop(self):
        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self.rpc_conn.close()
        except Exception:
            pass

        super(Service, self).stop()

    def _setup_subscriptions(self):
        """
        Set's up subscriptions for the various exchange+topic combinations that
        we have a handler for.
        """
        for handler in self.handlers:
            exchange, topics = handler.get_exchange_topics()

            for topic in topics:
                queue_name = "designate.notifications.%s.%s.%s" % (
                    handler.get_canonical_name(), exchange, topic)

                self.rpc_conn.join_consumer_pool(
                    self._process_notification,
                    queue_name,
                    topic,
                    exchange_name=exchange)

    def _get_handler_event_types(self):
        event_types = set()
        for handler in self.handlers:
            for et in handler.get_event_types():
                event_types.add(et)
        return event_types

    def _process_notification(self, notification):
        """
        Processes an incoming notification, offering each extension the
        opportunity to handle it.
        """
        event_type = notification.get('event_type')

        # NOTE(zykes): Only bother to actually do processing if there's any
        # matching events, skips logging of things like compute.exists etc.
        if event_type in self._get_handler_event_types():
            for handler in self.handlers:
                self._process_notification_for_handler(handler, notification)

    def _process_notification_for_handler(self, handler, notification):
        """
        Processes an incoming notification for a specific handler, checking
        to see if the handler is interested in the notification before
        handing it over.
        """
        event_type = notification['event_type']
        payload = notification['payload']

        if event_type in handler.get_event_types():
            LOG.debug('Found handler for: %s' % event_type)
            handler.process_notification(event_type, payload)
