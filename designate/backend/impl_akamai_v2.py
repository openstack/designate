# Copyright 2019 Cloudification GmbH
#
# Author: Sergey Kraynev <contact@cloudification.io>
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

import time
from urllib import parse as urlparse

from oslo_log import log as logging
from oslo_utils import importutils
import requests

from designate.backend import base
from designate import exceptions


LOG = logging.getLogger(__name__)


class AkamaiClient:
    def __init__(self, client_token=None, client_secret=None,
                 access_token=None, host=None):
        session = requests.Session()
        self.baseurl = 'https://%s' % host
        self.client_token = client_token
        self.client_secret = client_secret
        self.access_token = access_token

        edgegrid = importutils.try_import('akamai.edgegrid')
        if not edgegrid:
            raise exceptions.Backend('The edgegrid library is not available')

        session.auth = edgegrid.EdgeGridAuth(
            client_token=self.client_token,
            client_secret=self.client_secret,
            access_token=self.access_token
        )

        self.http = session

    def gen_url(self, url_path):
        return urlparse.urljoin(self.baseurl, url_path)

    def post(self, payloads):
        url_path = payloads.pop('url')
        return self.http.post(url=self.gen_url(url_path), **payloads)

    def get(self, url_path):
        return self.http.get(url=self.gen_url(url_path))

    def build_masters_field(self, masters):
        # Akamai v2 supports only ip and hostnames. Ports could not be
        # specified explicitly. 53 will be used by default
        return [master.host for master in masters]

    def gen_tsig_payload(self, target):
        return {
            'name': target.options.get('tsig_key_name'),
            'algorithm': target.options.get('tsig_key_algorithm'),
            'secret': target.options.get('tsig_key_secret'),
        }

    def gen_create_payload(self, zone, masters, contract_id, gid, tenant_id,
                           target):
        if contract_id is None:
            raise exceptions.Backend(
                'contractId is required for zone creation')

        masters = self.build_masters_field(masters)
        body = {
            'zone': zone['name'],
            'type': 'secondary',
            'comment': 'Created by Designate for Tenant %s' % tenant_id,
            'masters': masters,
        }
        # Add tsigKey if it exists
        if target.options.get('tsig_key_name'):
            # It's not mentioned in doc, but json schema supports specification
            # TsigKey in the same zone creation body
            body.update({'tsigKey': self.gen_tsig_payload(target)})

        params = {
            'contractId': contract_id,
            'gid': gid,
        }
        return {
            'url': 'config-dns/v2/zones',
            'params': params,
            'json': body,
        }

    def create_zone(self, payload):
        result = self.post(payload)
        # NOTE: ignore error about duplicate SZ in AKAMAI
        if result.status_code == 409 and result.reason == 'Conflict':
            LOG.info("Can't create zone %s because it already exists",
                     payload['json']['zone'])

        elif not result.ok:
            json_res = result.json()
            raise exceptions.Backend(
                'Zone creation failed due to: %s' % json_res['detail'])

    @staticmethod
    def gen_delete_payload(zone_name, force):
        return {
            'url': '/config-dns/v2/zones/delete-requests',
            'params': {'force': force},
            'json': {'zones': [zone_name]},
        }

    def delete_zone(self, zone_name):
        # - try to delete with force=True
        # - if we get Forbidden error - try to delete it with Checks logic

        result = self.post(
            self.gen_delete_payload(zone_name, force=True))

        if result.status_code == 403 and result.reason == 'Forbidden':
            result = self.post(
                self.gen_delete_payload(zone_name, force=False))
            if result.ok:
                request_id = result.json().get('requestId')
                LOG.info('Run soft delete for zone (%s) and requestId (%s)',
                         zone_name, request_id)

                if request_id is None:
                    reason = 'requestId missed in response'
                    raise exceptions.Backend(
                        'Zone deletion failed due to: %s' % reason)

                self.validate_deletion_is_complete(request_id)

        if not result.ok and result.status_code != 404:
            reason = result.json().get('detail') or result.json()
            raise exceptions.Backend(
                'Zone deletion failed due to: %s' % reason)

    def validate_deletion_is_complete(self, request_id):
        check_url = '/config-dns/v2/zones/delete-requests/%s' % request_id
        deleted = False
        attempt = 0
        while not deleted and attempt < 10:
            result = self.get(check_url)
            deleted = result.json()['isComplete']
            attempt += 1
            time.sleep(1.0)

        if not deleted:
            raise exceptions.Backend(
                'Zone was not deleted after %s attempts' % attempt)


class AkamaiBackend(base.Backend):
    __plugin_name__ = 'akamai_v2'

    __backend_status__ = 'untested'

    def __init__(self, target):
        super().__init__(target)

        self.client = self.init_client()

    def init_client(self):
        baseurl = self.options.get('akamai_host', '127.0.0.1')
        client_token = self.options.get('akamai_client_token', 'admin')
        client_secret = self.options.get('akamai_client_secret', 'admin')
        access_token = self.options.get('akamai_access_token', 'admin')

        return AkamaiClient(client_token, client_secret, access_token, baseurl)

    def create_zone(self, context, zone):
        """Create a DNS zone"""
        LOG.debug('Create Zone')
        contract_id = self.options.get('akamai_contract_id')
        gid = self.options.get('akamai_gid')
        project_id = context.project_id or zone.tenant_id
        # Take list of masters from pools.yaml
        payload = self.client.gen_create_payload(
            zone, self.masters, contract_id, gid, project_id, self.target)
        self.client.create_zone(payload)

    def delete_zone(self, context, zone, zone_params=None):
        """Delete a DNS zone"""
        LOG.debug('Delete Zone')
        self.client.delete_zone(zone['name'])
