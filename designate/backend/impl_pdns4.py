# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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
from six.moves import urllib

import requests
from oslo_log import log as logging
from oslo_config import cfg

from designate import exceptions
from designate.backend import base


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class PDNS4Backend(base.Backend):
    __plugin_name__ = 'pdns4'

    __backend_status__ = 'release-compatible'

    def __init__(self, target):
        super(PDNS4Backend, self).__init__(target)

        self.api_endpoint = self.options.get('api_endpoint')
        self.api_token = self.options.get('api_token')

    def _build_url(self, zone=''):
        r_url = urllib.parse.urlparse(self.api_endpoint)
        return "%s://%s/api/v1/servers/localhost/zones%s%s" % (
            r_url.scheme, r_url.netloc, '/' if zone else '', zone)

    def create_zone(self, context, zone):
        """Create a DNS zone"""

        masters = \
            ['%s:%d' % (master.host, master.port) for master in self.masters]

        data = {
            "name": zone.name,
            "kind": "slave",
            "masters": masters,

        }
        headers = {
            "X-API-Key": self.api_token
        }

        try:
            requests.post(
                self._build_url(),
                json=data,
                headers=headers
            ).raise_for_status()
        except requests.HTTPError as e:
            raise exceptions.Backend(e)

    def delete_zone(self, context, zone):
        """Delete a DNS zone"""

        headers = {
            "X-API-Key": self.api_token
        }

        try:
            requests.delete(
                self._build_url(zone.name),
                headers=headers
            ).raise_for_status()
        except requests.HTTPError as e:
            raise exceptions.Backend(e)
