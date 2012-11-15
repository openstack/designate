# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
# Author: Endre Karlson <endre.karlson@bouvet.no>
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
import abc
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.context import MonikerContext
from moniker.plugin import Plugin
from moniker import exceptions


LOG = logging.getLogger(__name__)


def get_ip_data(addr_dict):
    ip = addr_dict['address']
    version = addr_dict['version']

    data = {
        'ip_version': version
    }

    # TODO: Add v6 support
    if version == 4:
        data['ip_address'] = ip.replace('.', '-')
        ip_data = ip.split(".")
        for i in [0, 1, 2, 3]:
            data["octet%s" % i] = ip_data[i]
    return data


class Handler(Plugin):
    """ Base class for notification handlers """
    __plugin_type__ = 'handler'

    def __init__(self, central_service):
        super(Handler, self).__init__()
        LOG.debug('Loaded handler: %s' % __name__)
        self.central_service = central_service

    @abc.abstractmethod
    def get_exchange_topics(self):
        """
        Returns a tuple of (exchange, list(topics)) this handler wishes
        to receive notifications from.
        """

    @abc.abstractmethod
    def get_event_types(self):
        """
        Returns a list of event types this handler is capable of  processing
        """

    @abc.abstractmethod
    def process_notification(self, event_type, payload):
        """ Processes a given notification """

    @classmethod
    def get_opts(cls):
        return [cfg.StrOpt('domain_id', default=None)]

    def get_domain(self, domain_id):
        """
        Return the domain for this context
        """
        context = MonikerContext.get_admin_context()
        return self.central_service.get_domain(context, domain_id)


class BaseAddressHandler(Handler):
    default_format = '%(octet0)s-%(octet1)s-%(octet2)s-%(octet3)s.%(domain)s'

    def _create(self, addresses, extra, managed=True,
                resource_type=None, resource_id=None):
        """
        Create a a record from addresses

        :param addresses: Address objects like
                          {'version': 4, 'ip': '10.0.0.1'}
        :param extra: Extra data to use when formatting the record
        :param managed: Is it a managed resource
        :param resource_type: The managed resource type
        :param resource_id: The managed resource ID
        """
        domain = self.get_domain(self.config.domain_id)

        data = extra.copy()
        data['domain'] = domain['name']

        context = MonikerContext.get_admin_context()

        for addr in addresses:
            record_data = data.copy()
            record_data.update(get_ip_data(addr))

            record_name = self.default_format % record_data
            record_values = {
                'type': 'A' if addr['version'] == 4 else 'AAAA',
                'name': record_name,
                'data': addr['address']}
            if managed:
                record_values.update({
                    'managed_resource': managed,
                    'managed_resource_type': resource_type,
                    'managed_resource_id': resource_id})
            self.central_service.create_record(context, domain['id'],
                                               record_values)

    def _delete(self, managed=True, resource_id=None, resource_type='instance',
                criterion={}):
        """
        Handle a generic delete of a fixed ip within a domain

        :param criterion: Criterion to search and destroy records
        """
        context = MonikerContext.get_admin_context()

        if managed:
            criterion.update({
                'managed_resource': managed,
                'managed_resource_id': resource_id,
                'managed_resource_type': resource_type
            })

        records = self.central_service.get_records(context,
                                                   self.config.domain_id,
                                                   criterion)
        for record in records:
            LOG.debug('Deleting record %s' % record['id'])
            self.central_service.delete_record(context, self.config.domain_id,
                                               record['id'])
