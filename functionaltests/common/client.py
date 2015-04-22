"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from tempest_lib.common.rest_client import RestClient
from tempest_lib.auth import KeystoneV2Credentials
from tempest_lib.auth import KeystoneV2AuthProvider
from config import cfg
from noauth import NoAuthAuthProvider


class DesignateClient(RestClient):

    def __init__(self):
        if cfg.CONF.noauth.use_noauth:
            auth_provider = self._get_noauth_auth_provider()
        else:
            auth_provider = self._get_keystone_auth_provider()
        super(DesignateClient, self).__init__(
            auth_provider=auth_provider,
            service='dns',
            region=cfg.CONF.identity.region,
        )

    def _get_noauth_auth_provider(self):
        creds = KeystoneV2Credentials(
            tenant_id=cfg.CONF.noauth.tenant_id,
        )
        return NoAuthAuthProvider(creds, cfg.CONF.noauth.designate_endpoint)

    def _get_keystone_auth_provider(self):
        creds = KeystoneV2Credentials(
            username=cfg.CONF.identity.admin_username,
            password=cfg.CONF.identity.admin_password,
            tenant_name=cfg.CONF.identity.admin_tenant_name,
        )
        auth_provider = KeystoneV2AuthProvider(creds, cfg.CONF.identity.uri)
        auth_provider.fill_credentials()
        return auth_provider
