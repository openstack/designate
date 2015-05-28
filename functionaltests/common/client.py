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

import abc

from config import cfg
from noauth import NoAuthAuthProvider
from tempest_lib.common.rest_client import RestClient
from tempest_lib.auth import KeystoneV2Credentials
from tempest_lib.auth import KeystoneV2AuthProvider

from functionaltests.common.utils import memoized


class BaseDesignateClient(RestClient):

    def __init__(self):
        super(BaseDesignateClient, self).__init__(
            auth_provider=self.get_auth_provider(),
            service='dns',
            region=cfg.CONF.identity.region
        )

    def get_auth_provider(self):
        if cfg.CONF.noauth.use_noauth:
            return self._get_noauth_auth_provider()
        return self._get_keystone_auth_provider()

    @abc.abstractmethod
    def _get_noauth_auth_provider(self):
        pass

    @abc.abstractmethod
    def _get_keystone_auth_provider(self):
        pass


class DesignateClient(BaseDesignateClient):
    """Client with default user"""

    def _get_noauth_auth_provider(self):
        creds = KeystoneV2Credentials(
            tenant_id=cfg.CONF.noauth.tenant_id,
        )
        return NoAuthAuthProvider(creds, cfg.CONF.noauth.designate_endpoint)

    def _get_keystone_auth_provider(self):
        creds = KeystoneV2Credentials(
            username=cfg.CONF.identity.username,
            password=cfg.CONF.identity.password,
            tenant_name=cfg.CONF.identity.tenant_name,
        )
        auth_provider = KeystoneV2AuthProvider(creds, cfg.CONF.identity.uri)
        auth_provider.fill_credentials()
        return auth_provider


class DesignateAltClient(BaseDesignateClient):
    """Client with alternate user"""

    def _get_noauth_auth_provider(self):
        creds = KeystoneV2Credentials(
            tenant_id=cfg.CONF.noauth.alt_tenant_id,
        )
        return NoAuthAuthProvider(creds, cfg.CONF.noauth.designate_endpoint)

    def _get_keystone_auth_provider(self):
        creds = KeystoneV2Credentials(
            username=cfg.CONF.identity.alt_username,
            password=cfg.CONF.identity.alt_password,
            tenant_name=cfg.CONF.identity.alt_tenant_name,
        )
        auth_provider = KeystoneV2AuthProvider(creds, cfg.CONF.identity.uri)
        auth_provider.fill_credentials()
        return auth_provider


class DesignateAdminClient(BaseDesignateClient):
    """Client with admin user"""

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


class ClientMixin(object):

    @classmethod
    @memoized
    def get_clients(cls):
        return {
            'default': DesignateClient(),
            'alt': DesignateAltClient(),
            'admin': DesignateAdminClient(),
        }

    def __init__(self, client):
        self.client = client

    @classmethod
    def deserialize(cls, resp, body, model_type):
        return resp, model_type.from_json(body)

    @classmethod
    def as_user(cls, user):
        """
        :param user: 'default', 'alt', or 'admin'
        """
        return cls(cls.get_clients()[user])

    @property
    def tenant_id(self):
        return self.client.tenant_id
