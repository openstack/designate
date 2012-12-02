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
from moniker.openstack.common import rpc
from moniker.openstack.common.rpc import service as rpc_service
from stevedore.named import NamedExtensionManager
from moniker import policy
from moniker import storage
from moniker import utils
from moniker import backend

LOG = logging.getLogger(__name__)

HANDLER_NAMESPACE = 'moniker.notification.handler'

cfg.CONF.register_opts([
    cfg.ListOpt('enabled-notification-handlers', default=[],
                help='Enabled Notification Handlers'),
])


class Service(rpc_service.Service):
    def __init__(self, *args, **kwargs):

        self.backend = backend.get_backend(cfg.CONF)

        kwargs.update(
            host=cfg.CONF.host,
            topic=cfg.CONF.central_topic,
        )

        policy.init_policy()

        super(Service, self).__init__(*args, **kwargs)

        # Get a storage connection
        self.storage_conn = storage.get_connection(cfg.CONF)

        # Initialize extensions
        self.handlers = self._init_extensions()

        if self.handlers:
            # Get a rpc connection if needed
            self.rpc_conn = rpc.create_connection()

    def _init_extensions(self):
        """ Loads and prepares all enabled extensions """
        self.extensions_manager = NamedExtensionManager(
            HANDLER_NAMESPACE, names=cfg.CONF.enabled_notification_handlers)

        def _load_extension(ext):
            handler_cls = ext.plugin
            handler_cls.register_opts(cfg.CONF)
            return handler_cls(central_service=self)

        try:
            return self.extensions_manager.map(_load_extension)
        except RuntimeError:
            # No handlers enabled. No problem.
            return []

    def start(self):
        self.backend.start()
        super(Service, self).start()

        if self.handlers:
            # Setup notification subscriptions and start consuming
            self._setup_subscriptions()
            self.rpc_conn.consume_in_thread_group(self.tg)

    def stop(self):
        if self.handlers:
            # Try to shut the connection down, but if we get any sort of
            # errors, go ahead and ignore them.. as we're shutting down anyway
            try:
                self.rpc_conn.close()
            except Exception:
                pass

        super(Service, self).stop()
        self.backend.stop()

    def _setup_subscriptions(self):
        """
        Set's up subscriptions for the various exchange+topic combinations that
        we have a handler for.
        """
        for handler in self.handlers:
            exchange, topics = handler.get_exchange_topics()

            for topic in topics:
                queue_name = "moniker.notifications.%s.%s" % (exchange, topic)

                self.rpc_conn.declare_topic_consumer(
                    queue_name=queue_name,
                    topic=topic,
                    exchange_name=exchange,
                    callback=self._process_notification)

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

    # Server Methods
    def create_server(self, context, values):
        policy.check('create_server', context)

        server = self.storage_conn.create_server(context, values)

        utils.notify(context, 'api', 'server.create', server)

        return server

    def get_servers(self, context, criterion=None):
        policy.check('get_servers', context)

        return self.storage_conn.get_servers(context, criterion)

    def get_server(self, context, server_id):
        policy.check('get_server', context, {'server_id': server_id})

        return self.storage_conn.get_server(context, server_id)

    def update_server(self, context, server_id, values):
        policy.check('update_server', context, {'server_id': server_id})

        server = self.storage_conn.update_server(context, server_id, values)

        utils.notify(context, 'api', 'server.update', server)

        return server

    def delete_server(self, context, server_id):
        policy.check('delete_server', context, {'server_id': server_id})

        server = self.storage_conn.get_server(context, server_id)

        utils.notify(context, 'api', 'server.delete', server)

        return self.storage_conn.delete_server(context, server_id)

    # Domain Methods
    def create_domain(self, context, values):
        if 'tenant_id' not in values:
            values['tenant_id'] = None

        target = {'tenant_id': values['tenant_id']}
        policy.check('create_domain', context, target)

        domain = self.storage_conn.create_domain(context, values)

        self.backend.create_domain(context, domain)
        utils.notify(context, 'api', 'domain.create', domain)

        return domain

    def get_domains(self, context, criterion=None):
        policy.check('get_domains', context, {'tenant_id': context.tenant_id})

        if criterion is None:
            criterion = {}

        if context.tenant_id is not None:
            criterion['tenant_id'] = context.tenant_id

        return self.storage_conn.get_domains(context, criterion)

    def get_domain(self, context, domain_id):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {'domain_id': domain_id, 'tenant_id': domain['tenant_id']}
        policy.check('get_domain', context, target)

        return domain

    def update_domain(self, context, domain_id, values):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {'domain_id': domain_id, 'tenant_id': domain['tenant_id']}
        policy.check('update_domain', context, target)

        domain = self.storage_conn.update_domain(context, domain_id, values)

        self.backend.update_domain(context, domain)
        utils.notify(context, 'api', 'domain.update', domain)

        return domain

    def delete_domain(self, context, domain_id):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {'domain_id': domain_id, 'tenant_id': domain['tenant_id']}
        policy.check('delete_domain', context, target)

        self.backend.delete_domain(context, domain)
        utils.notify(context, 'api', 'domain.delete', domain)

        return self.storage_conn.delete_domain(context, domain_id)

    # Record Methods
    def create_record(self, context, domain_id, values):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {'domain_id': domain_id, 'tenant_id': domain['tenant_id']}
        policy.check('create_record', context, target)

        record = self.storage_conn.create_record(context, domain_id, values)

        self.backend.create_record(context, domain, record)
        utils.notify(context, 'api', 'record.create', record)

        return record

    def get_records(self, context, domain_id, criterion=None):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {'domain_id': domain_id, 'tenant_id': domain['tenant_id']}
        policy.check('get_records', context, target)

        return self.storage_conn.get_records(context, domain_id, criterion)

    def get_record(self, context, domain_id, record_id):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {'domain_id': domain_id, 'tenant_id': domain['tenant_id']}
        policy.check('get_record', context, target)

        return self.storage_conn.get_record(context, record_id)

    def update_record(self, context, domain_id, record_id, values):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'record_id': record_id,
            'tenant_id': domain['tenant_id']
        }
        policy.check('update_record', context, target)

        record = self.storage_conn.update_record(context, record_id, values)

        self.backend.update_record(context, domain, record)
        utils.notify(context, 'api', 'record.update', record)

        return record

    def delete_record(self, context, domain_id, record_id):
        domain = self.storage_conn.get_domain(context, domain_id)

        target = {
            'domain_id': domain_id,
            'record_id': record_id,
            'tenant_id': domain['tenant_id']
        }
        policy.check('delete_record', context, target)

        record = self.storage_conn.get_record(context, record_id)

        self.backend.delete_record(context, domain, record)
        utils.notify(context, 'api', 'record.delete', record)

        return self.storage_conn.delete_record(context, record_id)
