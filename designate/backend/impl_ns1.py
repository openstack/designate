# Copyright 2021 NS1 Inc. https://www.ns1.com
#
# Author: Dragan Blagojevic <dblagojevic@daitan.com>
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
from oslo_log import log as logging
import requests

from designate.backend import base
import designate.conf
from designate import exceptions


LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF


class NS1Backend(base.Backend):
    __plugin_name__ = 'ns1'

    __backend_status__ = 'untested'

    def __init__(self, target):
        super().__init__(target)

        self.api_endpoint = 'https://' + self.options.get('api_endpoint')
        self.api_token = self.options.get('api_token')
        self.tsigkey_name = self.options.get('tsigkey_name', None)
        self.tsigkey_hash = self.options.get('tsigkey_hash', None)
        self.tsigkey_value = self.options.get('tsigkey_value', None)

        self.headers = {
            'X-NSONE-Key': self.api_token
        }

    def _build_url(self, zone):
        return '{}/v1/zones/{}'.format(
            self.api_endpoint, zone.name.rstrip('.')
        )

    def _get_master(self):
        try:
            return self.masters[0]
        except IndexError as e:
            LOG.error('No masters host set in pools.yaml')
            raise exceptions.Backend(e)

    def _check_zone_exists(self, zone):
        try:
            requests.get(
                self._build_url(zone),
                headers=self.headers
            ).raise_for_status()
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                LOG.error('HTTP error in check zone exists. Zone %s', zone)
                raise exceptions.Backend(e)
        except requests.ConnectionError as e:
            LOG.error('Connection error in check zone exists. Zone %s', zone)
            raise exceptions.Backend(e)

        return True

    def create_zone(self, context, zone):
        master = self._get_master()
        # designate requires "." at end of zone name, NS1 requires omitting
        data = {
            'zone': zone.name.rstrip('.'),
            'secondary': {
                'enabled': True,
                'primary_ip': master.host,
                'primary_port': master.port
            }
        }
        if self.tsigkey_name:
            tsig = {
                'enabled': True,
                'hash': self.tsigkey_hash,
                'name': self.tsigkey_name,
                'key': self.tsigkey_value
            }
            data['secondary']['tsig'] = tsig

        if not self._check_zone_exists(zone):
            try:
                requests.put(
                    self._build_url(zone),
                    json=data,
                    headers=self.headers
                ).raise_for_status()
            except requests.HTTPError as e:
                # check if the zone was actually created
                if self._check_zone_exists(zone):
                    LOG.info(
                        '%s was created with an error. Deleting zone',
                        zone.name
                    )
                    try:
                        self.delete_zone(context, zone)
                    except exceptions.Backend:
                        LOG.error(
                            'Could not delete errored zone %s', zone.name
                        )
                raise exceptions.Backend(e)
        else:
            LOG.info(
                "Can't create zone %s because it already exists", zone.name
            )

    def delete_zone(self, context, zone, zone_params=None):
        """Delete a DNS zone"""

        # First verify that the zone exists
        if self._check_zone_exists(zone):
            try:
                requests.delete(
                    self._build_url(zone),
                    headers=self.headers
                ).raise_for_status()
            except requests.HTTPError as e:
                raise exceptions.Backend(e)
        else:
            LOG.warning(
                'Trying to delete zone %s but that zone is not present in the '
                'ns1 backend. Assuming success.', zone
            )
