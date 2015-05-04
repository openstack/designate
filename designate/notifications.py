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

from oslo_config import cfg
from oslo_log import log as logging

from designate import rpc

LOG = logging.getLogger(__name__)

notify_opts = [
    cfg.BoolOpt('notify_api_faults', default=False,
                help='Send notifications if there\'s a failure in the API.')
]

CONF = cfg.CONF
CONF.register_opts(notify_opts)


def send_api_fault(context, url, status, exception):
    """Send an api.fault notification."""

    if not CONF.notify_api_faults:
        return

    payload = {'url': url, 'exception': str(exception), 'status': status}

    rpc.get_notifier('api').error(context, 'dns.api.fault', payload)
