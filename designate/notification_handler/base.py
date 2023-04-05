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

from oslo_config import cfg
from oslo_log import log as logging

import re

from designate import exceptions
from designate.central import rpcapi as central_rpcapi
from designate.context import DesignateContext
from designate.objects import Record
from designate.objects import RecordList
from designate.objects import RecordSet
from designate.plugin import ExtensionPlugin

LOG = logging.getLogger(__name__)


class NotificationHandler(ExtensionPlugin):
    """Base class for notification handlers"""
    __plugin_ns__ = 'designate.notification.handler'
    __plugin_type__ = 'handler'

    def __init__(self, *args, **kw):
        super(NotificationHandler, self).__init__(*args, **kw)
        self.central_api = central_rpcapi.CentralAPI()

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
    def process_notification(self, context, event_type, payload):
        """Processes a given notification"""

    def get_zone(self, zone_id):
        """
        Return the zone for this context
        """
        context = DesignateContext.get_admin_context(all_tenants=True)
        return self.central_api.get_zone(context, zone_id)

    def _create_or_update_recordset(self, context, records, zone_id, name,
                                    type, ttl=None):
        name = name.encode('idna').decode('utf-8')

        try:
            # Attempt to create a new recordset.
            values = {
                'name': name,
                'type': type,
                'ttl': ttl,
            }
            recordset = RecordSet(**values)
            recordset.records = RecordList(objects=records)
            recordset.validate()
            recordset = self.central_api.create_recordset(
                context, zone_id, recordset
            )
        except exceptions.DuplicateRecordSet:
            # Fetch and update the existing recordset.
            recordset = self.central_api.find_recordset(context, {
                'zone_id': zone_id,
                'name': name,
                'type': type,
            })
            for record in records:
                recordset.records.append(record)
            recordset.validate()
            recordset = self.central_api.update_recordset(
                context, recordset
            )
        LOG.debug('Creating record in %s / %s', zone_id, recordset['id'])
        return recordset

    def _update_or_delete_recordset(self, context, zone_id, recordset_id,
                                    record_to_delete_id):
        LOG.debug(
            'Deleting record in %s / %s',
            zone_id, record_to_delete_id
        )

        try:
            recordset = self.central_api.find_recordset(
                context, {'id': recordset_id, 'zone_id': zone_id}
            )
            record_ids = [record['id'] for record in recordset.records]

            # Record no longer in recordset. Let's abort.
            if record_to_delete_id not in record_ids:
                LOG.debug(
                    'Record %s not found in recordset %s',
                    record_to_delete_id, recordset_id
                )
                return

            # Remove the record from the recordset.
            for record in list(recordset.records):
                if record['id'] != record_to_delete_id:
                    continue
                recordset.records.remove(record)
                break

            if not recordset.records:
                # Recordset is now empty. Remove it.
                self.central_api.delete_recordset(
                    context, zone_id, recordset_id
                )
                return

            # Recordset still has records, validate it and update it.
            recordset.validate()
            self.central_api.update_recordset(context, recordset)
        except exceptions.RecordSetNotFound:
            LOG.info(
                'Recordset %s for record %s was already removed',
                recordset_id, record_to_delete_id
            )


class BaseAddressHandler(NotificationHandler):
    default_formatv4 = ('%(hostname)s.%(domain)s',)
    default_formatv6 = ('%(hostname)s.%(domain)s',)

    def _get_ip_data(self, addr_dict):
        ip = addr_dict['address']
        version = addr_dict['version']

        data = {
            'ip_version': version,
        }

        if version == 4:
            data['ip_address'] = ip.replace('.', '-')
            ip_data = ip.split(".")
            for i in [0, 1, 2, 3]:
                data["octet%s" % i] = ip_data[i]
        if version == 6:
            data['ip_address'] = ip.replace(':', '-')
            ip_data = re.split('::|:', ip)
            for i in range(len(ip_data)):
                data["octet%s" % i] = ip_data[i]
        return data

    def _get_formatv4(self):
        return (
            cfg.CONF[self.name].get('formatv4') or
            self.default_formatv4
        )

    def _get_formatv6(self):
        return (
            cfg.CONF[self.name].get('formatv6') or
            self.default_formatv6
        )

    def _create(self, addresses, extra, zone_id, resource_type=None,
                resource_id=None):
        """
        Create a record from addresses

        :param addresses: Address objects like
                          {'version': 4, 'ip': '10.0.0.1'}
        :param extra: Extra data to use when formatting the record
        :param zone_id: The ID of the designate zone.
        :param resource_type: The managed resource type
        :param resource_id: The managed resource ID
        """
        LOG.debug('Using Zone ID: %s', zone_id)
        zone = self.get_zone(zone_id)
        LOG.debug('Domain: %r', zone)

        data = extra.copy()
        LOG.debug('Event data: %s', data)
        data['zone'] = zone['name']

        context = DesignateContext().elevated()
        context.all_tenants = True
        context.edit_managed_records = True

        for addr in addresses:
            event_data = data.copy()
            event_data.update(self._get_ip_data(addr))

            if addr['version'] == 4:
                format = self._get_formatv4()
            else:
                format = self._get_formatv6()

            for fmt in format:
                recordset_values = {
                    'zone_id': zone['id'],
                    'name': fmt % event_data,
                    'type': 'A' if addr['version'] == 4 else 'AAAA'}

                record_values = {
                    'data': addr['address'],
                    'managed': True,
                    'managed_plugin_name': self.get_plugin_name(),
                    'managed_plugin_type': self.get_plugin_type(),
                    'managed_resource_type': resource_type,
                    'managed_resource_id': resource_id
                }
                self._create_or_update_recordset(
                    context, [Record(**record_values)], **recordset_values
                )

    def _delete(self, zone_id, resource_id=None, resource_type='instance',
                criterion=None):
        """
        Handle a generic delete of a fixed ip within a zone

        :param zone_id: The ID of the designate zone.
        :param resource_id: The managed resource ID
        :param resource_type: The managed resource type
        :param criterion: Criterion to search and destroy records
        """
        criterion = criterion or {}

        context = DesignateContext().elevated()
        context.all_tenants = True
        context.edit_managed_records = True

        criterion.update({
            'zone_id': zone_id,
            'managed': True,
            'managed_plugin_name': self.get_plugin_name(),
            'managed_plugin_type': self.get_plugin_type(),
            'managed_resource_id': resource_id,
            'managed_resource_type': resource_type
        })

        records = self.central_api.find_records(context, criterion)
        for record in records:
            self._update_or_delete_recordset(
                context, zone_id, record['recordset_id'], record['id']
            )
