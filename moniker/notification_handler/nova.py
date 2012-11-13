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
from moniker import exceptions
from moniker.context import MonikerContext
from moniker.notification_handler.base import Handler

LOG = logging.getLogger(__name__)


class NovaHandler(Handler):
    """ Hanlder for Nova's notifications """

    def __init__(self, *args, **kwargs):
        super(NovaHandler, self).__init__(*args, **kwargs)

        self.fixed_ip_domain = cfg.CONF.nova_fixed_ip_domain

        if not self.fixed_ip_domain:
            msg = ('nova_fixed_ip_domain must be configured to use the nova '
                   'handler')
            raise exceptions.ConfigurationError(msg)

    @staticmethod
    def register_opts(conf):
        conf.register_opts([
            cfg.StrOpt('nova-fixed-ip-domain', default=None),
            cfg.IntOpt('nova-control-exchange', default='nova'),
            cfg.ListOpt('nova-notification-topics', default=['monitor'])
        ])

    def get_exchange_topics(self):
        exchange = cfg.CONF.nova_control_exchange

        topics = [topic + ".info"
                  for topic in cfg.CONF.nova_notification_topics]

        return (exchange, topics)

    def get_event_types(self):
        return [
            'compute.instance.create.end',
            'compute.instance.delete.start',
            # 'compute.instance.rebuild.start',  # Needed?
            # 'compute.instance.rebuild.end',    # Needed?
            # 'compute.instance.exists',         # Needed?
            # 'network.floating_ip.allocate',    # Needed?
            # 'network.floating_ip.deallocate',  # Needed?
            'network.floating_ip.associate',
            'network.floating_ip.disassociate',
        ]

    def process_notification(self, event_type, payload):
        LOG.debug('NovaHandler recieved notification - %s' % event_type)

        if event_type == 'compute.instance.create.end':
            return self.handle_instance_create(payload)

        elif event_type == 'compute.instance.delete.start':
            return self.handle_instance_delete(payload)

        elif event_type == 'network.floating_ip.associate':
            return self.handle_floating_ip_associate(payload)

        elif event_type == 'network.floating_ip.disassociate':
            return self.handle_floating_ip_disassociate(payload)

        else:
            raise ValueError('NovaHandler recieved an invalid event type')

    def handle_instance_create(self, payload):
        context = MonikerContext.get_admin_context()

        # Fetch the FixedIP Domain
        fixed_ip_domain = self.central_service.get_domain(context,
                                                          self.fixed_ip_domain)

        # For each fixed ip, create an associated record.
        for fixed_ip in payload['fixed_ips']:
            record_name = '%(instance_id)s.%(tenant_id)s.%(domain)s' % dict(
                instance_id=payload['instance_id'],
                tenant_id=payload['tenant_id'],
                domain=fixed_ip_domain['name'])

            record_values = {
                'type': 'A' if fixed_ip['version'] == 4 else 'AAAA',
                'name': record_name,
                'data': fixed_ip['address'],

                'managed_resource': True,
                'managed_resource_type': u'instance',
                'managed_resource_id': payload['instance_id'],
            }

            self.central_service.create_record(context, self.fixed_ip_domain,
                                               record_values)

    def handle_instance_delete(self, payload):
        context = MonikerContext.get_admin_context()

        # Fetch the instances managed records
        criterion = {
            'managed_resource': True,
            'managed_resource_type': u'instance',
            'managed_resource_id': payload['instance_id']
        }

        records = self.central_service.get_records(context,
                                                   self.fixed_ip_domain,
                                                   criterion)
        # Delete the matching records
        for record in records:
            LOG.debug('Deleting record %s' % record['id'])

            self.central_service.delete_record(context, self.fixed_ip_domain,
                                               record['id'])

    def handle_floating_ip_associate(self, payload):
        pass

    def handle_floating_ip_disassociate(self, payload):
        pass
