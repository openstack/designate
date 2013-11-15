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

from oslo.config import cfg

from designate.openstack.common import log as logging
from designate import notifier as notify

LOG = logging.getLogger(__name__)

notify_opts = [
    cfg.BoolOpt('notify_api_faults', default=False,
                help='Send notifications if there\'s a failure in the API.')
]

CONF = cfg.CONF
CONF.register_opts(notify_opts)
CONF.import_opt('default_notification_level',
                'designate.openstack.common.notifier.api')
CONF.import_opt('default_publisher_id',
                'designate.openstack.common.notifier.api')


def send_api_fault(url, status, exception):
    """Send an api.fault notification."""

    if not CONF.notify_api_faults:
        return

    payload = {'url': url, 'exception': str(exception), 'status': status}

    notify.get_notifier('api').error(None, 'dns.api.fault', payload)
