# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
#
# Copied: nova.notifications
import abc

from oslo_log import log as logging

import designate.conf
from designate import objects
from designate.plugin import DriverPlugin
from designate import rpc


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)
NOTIFICATION_PLUGIN = None


def send_api_fault(context, url, status, exception):
    """Send an api.fault notification."""

    if not CONF.notify_api_faults:
        return

    payload = {'url': url, 'exception': str(exception), 'status': status}

    rpc.get_notifier('api').error(context, 'dns.api.fault', payload)


def init_notification_plugin():
    LOG.debug("Loading notification plugin: %s", CONF.notification_plugin)
    cls = NotificationPlugin.get_driver(CONF.notification_plugin)

    global NOTIFICATION_PLUGIN
    NOTIFICATION_PLUGIN = cls()


def get_plugin():
    if NOTIFICATION_PLUGIN is None:
        init_notification_plugin()
    return NOTIFICATION_PLUGIN


class NotificationPlugin(DriverPlugin):
    """Base class for Notification Driver implementations"""
    __plugin_type__ = 'notification'
    __plugin_ns__ = 'designate.notification.plugin'

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def emit(self, notification_type, context, result, *args, **kwargs):
        """Return a payload to emit as part of the notification"""


class Default(NotificationPlugin):
    """Returns the result, as implemented in the base class"""
    __plugin_name__ = 'default'

    def emit(self, notification_type, context, result, *args, **kwargs):
        """Return the result of the function called"""
        return [result]


class Audit(NotificationPlugin):
    """Grabs Zone/Recordset names and RRData changes"""
    __plugin_name__ = 'audit'

    def zone_name(self, arglist, result):
        for arg in arglist + [result]:
            if isinstance(arg, objects.Zone):
                if arg.name is not None:
                    return arg.name
            if hasattr(arg, 'zone_name'):
                if arg.zone_name is not None:
                    return arg.zone_name

        return None

    def zone_id(self, arglist, result):
        for arg in arglist + [result]:
            if isinstance(arg, objects.Zone):
                if arg.id is not None:
                    return arg.id
            if hasattr(arg, 'zone_id'):
                if arg.zone_id is not None:
                    return arg.zone_id

        return None

    def recordset_name(self, arglist, result):
        for arg in arglist + [result]:
            if isinstance(arg, objects.RecordSet):
                if arg.name is not None:
                    return arg.name

        return None

    def recordset_data(self, arglist, result):
        if not isinstance(result, objects.RecordSet):
            return []

        for arg in arglist:
            if isinstance(arg, objects.RecordSet):
                if 'records' not in arg.obj_what_changed():
                    return []
                original_rrs = arg.obj_get_original_value('records')

                old_value = ' '.join(
                    [obj['data'] for obj in original_rrs])

                new_value = ' '.join(
                    [rr.data for rr in result.records])

                if old_value == new_value:
                    return []

                return [{
                    'change': 'records',
                    'old_value': old_value,
                    'new_value': new_value,
                }]

        return []

    def other_data(self, arglist, result):
        changes = []

        for arg in arglist:
            if not isinstance(arg, objects.DesignateObject):
                continue

            for change in arg.obj_what_changed():
                if change == 'records':
                    continue

                old_value = arg.obj_get_original_value(change)
                new_value = getattr(arg, change)

                # Just in case something odd makes it here
                if any(not isinstance(val, (int, float, bool, str, type(None)))
                       for val in (old_value, new_value)):
                    LOG.warning(
                        'Nulling notification values after unexpected values '
                        '(%s, %s)', old_value, new_value
                    )
                    old_value, new_value = None, None

                if old_value == new_value:
                    continue

                changes.append({
                    'change': change,
                    'old_value': str(old_value),
                    'new_value': str(new_value),
                })

        return changes

    def blank_event(self):
        return [{
            'change': None,
            'old_value': None,
            'new_value': None,
        }]

    def gather_changes(self, arglist, result, notification_type):
        changes = []

        if 'update' in notification_type:
            changes.extend(self.other_data(arglist, result))
            if notification_type == 'dns.recordset.update':
                changes.extend(self.recordset_data(arglist, result))
        elif 'create' in notification_type:
            if notification_type == 'dns.recordset.create':
                changes.extend(self.recordset_data(arglist, result))
            else:
                changes.extend(self.blank_event())
        else:
            changes.extend(self.blank_event())

        return changes

    def emit(self, notification_type, context, result, *args, **kwargs):
        arglist = []
        for item in args:
            if isinstance(item, tuple) or isinstance(item, list):
                arglist.extend(item)
            if isinstance(item, dict):
                arglist.extend(list(item.values()))

        payloads = []
        for change in self.gather_changes(arglist, result, notification_type):
            payloads.append({
                'zone_name': self.zone_name(arglist, result),
                'zone_id': self.zone_id(arglist, result),
                'recordset_name': self.recordset_name(arglist, result),
                'old_data': change['old_value'],
                'new_data': change['new_value'],
                'changed_field': change['change'],
            })

        return payloads
