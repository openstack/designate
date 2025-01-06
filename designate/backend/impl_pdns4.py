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
import ipaddress
import os.path
import urllib

from oslo_log import log as logging
import requests

from designate.backend import base
import designate.conf
from designate import exceptions


LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF


class PDNS4Backend(base.Backend):
    __plugin_name__ = 'pdns4'

    __backend_status__ = 'integrated'

    def __init__(self, target):
        super().__init__(target)

        self.api_endpoint = self.options.get('api_endpoint')
        self.api_token = self.options.get('api_token')
        self.tsigkey_name = self.options.get('tsigkey_name', None)
        self.api_ca_cert = self.options.get('api_ca_cert')

        self.headers = {
            "X-API-Key": self.api_token
        }

    def _build_url(self, zone=''):
        r_url = urllib.parse.urlparse(self.api_endpoint)
        return "{}://{}/api/v1/servers/localhost/zones{}{}".format(
            r_url.scheme, r_url.netloc, '/' if zone else '', zone)

    def _check_zone_exists(self, zone):
        zone = requests.get(
            self._build_url(zone=zone.name),
            headers=self.headers,
        )
        return zone.status_code == 200

    def _verify_ssl(self):
        """
        Function to check if variable has been declared.

        If the api_ca_cert is None, left blank or the default value 'changeme',
        returns False to disable ssl verification for the request.

        If api_ca_cert is defined, check if the file actually exists. If it
        does exist, return its value (should be the location of a CA
        certificate)
        """
        ca_cert = self.api_ca_cert

        if ca_cert is None or ca_cert == 'changeme' or ca_cert == '':
            return False
        if not os.path.exists(ca_cert):
            LOG.error("Could not find %s CA certificate."
                      "No such file or directory",
                      ca_cert)
            return False
        return ca_cert

    def create_zone(self, context, zone):
        """Create a DNS zone"""

        masters = []
        for master in self.masters:
            host = master.host
            try:
                if ipaddress.ip_address(host).version == 6:
                    host = '[%s]' % host
            except ValueError:
                pass
            masters.append('%s:%d' % (host, master.port))

        data = {
            "name": zone.name,
            "kind": "slave",
            "masters": masters,

        }
        if self.tsigkey_name:
            data['slave_tsig_key_ids'] = [self.tsigkey_name]

        if self._check_zone_exists(zone):
            LOG.info(
                '%s exists on the server. Deleting zone before creation', zone
            )

            try:
                self.delete_zone(context, zone)
            except exceptions.Backend:
                LOG.error('Could not delete pre-existing zone %s', zone)
                raise

        try:
            requests.post(
                self._build_url(),
                json=data,
                headers=self.headers,
                verify=self._verify_ssl()
            ).raise_for_status()
        except requests.HTTPError as e:
            # check if the zone was actually created - even with errors pdns
            # will create the zone sometimes
            if self._check_zone_exists(zone):
                LOG.info("%s was created with an error. Deleting zone", zone)
                try:
                    self.delete_zone(context, zone)
                except exceptions.Backend:
                    LOG.error('Could not delete errored zone %s', zone)
            raise exceptions.Backend(e)

    def delete_zone(self, context, zone, zone_params=None):
        """Delete a DNS zone"""

        # First verify that the zone exists -- If it's not present
        #  in the backend then we can just declare victory.
        if self._check_zone_exists(zone):
            try:
                requests.delete(
                    self._build_url(zone.name),
                    headers=self.headers
                ).raise_for_status()
            except requests.HTTPError as e:
                raise exceptions.Backend(e)
        else:
            LOG.warning("Trying to delete zone %s but that zone is not "
                        "present in the pdns backend. Assuming success.",
                        zone)
