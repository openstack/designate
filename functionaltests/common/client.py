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
from six import string_types
from six.moves.urllib.parse import quote_plus
from tempest_lib.common.rest_client import RestClient
from tempest_lib.auth import KeystoneV2Credentials
from tempest_lib.auth import KeystoneV2AuthProvider

from functionaltests.common.utils import memoized


class KeystoneV2AuthProviderWithOverridableUrl(KeystoneV2AuthProvider):

    def base_url(self, *args, **kwargs):
        # use the base url from the config if it was specified
        if cfg.CONF.identity.designate_override_url:
            return cfg.CONF.identity.designate_override_url
        else:
            return super(KeystoneV2AuthProviderWithOverridableUrl, self) \
                .base_url(*args, **kwargs)


class KeystoneV2AuthProviderNoToken(KeystoneV2AuthProviderWithOverridableUrl):

    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        _res = super(KeystoneV2AuthProviderNoToken, self)._decorate_request(
            filters, method, url, headers=headers, body=body,
            auth_data=auth_data)
        _url, _headers, _body = _res
        del _headers['X-Auth-Token']
        return (_url, _headers, _body)


class BaseDesignateClient(RestClient):

    def __init__(self, with_token=True):
        super(BaseDesignateClient, self).__init__(
            auth_provider=self.get_auth_provider(with_token),
            service='dns',
            region=cfg.CONF.identity.region
        )

    def get_auth_provider(self, with_token=True):
        if cfg.CONF.noauth.use_noauth:
            return self._get_noauth_auth_provider()
        return self._get_keystone_auth_provider(with_token)

    @abc.abstractmethod
    def _get_noauth_auth_provider(self):
        pass

    @abc.abstractmethod
    def _get_keystone_auth_provider(self):
        pass

    def _create_keystone_auth_provider(self, creds, with_token=True):
        if with_token:
            auth_provider = KeystoneV2AuthProviderWithOverridableUrl(
                creds, cfg.CONF.identity.uri)
        else:
            auth_provider = KeystoneV2AuthProviderNoToken(
                creds, cfg.CONF.identity.uri)
        auth_provider.fill_credentials()
        return auth_provider


class DesignateClient(BaseDesignateClient):
    """Client with default user"""

    def _get_noauth_auth_provider(self):
        creds = KeystoneV2Credentials(
            tenant_id=cfg.CONF.noauth.tenant_id,
        )
        return NoAuthAuthProvider(creds, cfg.CONF.noauth.designate_endpoint)

    def _get_keystone_auth_provider(self, with_token=True):
        creds = KeystoneV2Credentials(
            username=cfg.CONF.identity.username,
            password=cfg.CONF.identity.password,
            tenant_name=cfg.CONF.identity.tenant_name,
        )
        return self._create_keystone_auth_provider(creds, with_token)


class DesignateAltClient(BaseDesignateClient):
    """Client with alternate user"""

    def _get_noauth_auth_provider(self):
        creds = KeystoneV2Credentials(
            tenant_id=cfg.CONF.noauth.alt_tenant_id,
        )
        return NoAuthAuthProvider(creds, cfg.CONF.noauth.designate_endpoint)

    def _get_keystone_auth_provider(self, with_token=True):
        creds = KeystoneV2Credentials(
            username=cfg.CONF.identity.alt_username,
            password=cfg.CONF.identity.alt_password,
            tenant_name=cfg.CONF.identity.alt_tenant_name,
        )
        return self._create_keystone_auth_provider(creds, with_token)


class DesignateAdminClient(BaseDesignateClient):
    """Client with admin user"""

    def _get_noauth_auth_provider(self):
        creds = KeystoneV2Credentials(
            tenant_id=cfg.CONF.noauth.tenant_id,
        )
        return NoAuthAuthProvider(creds, cfg.CONF.noauth.designate_endpoint)

    def _get_keystone_auth_provider(self, with_token=True):
        creds = KeystoneV2Credentials(
            username=cfg.CONF.identity.admin_username,
            password=cfg.CONF.identity.admin_password,
            tenant_name=cfg.CONF.identity.admin_tenant_name,
        )
        return self._create_keystone_auth_provider(creds, with_token)


class ClientMixin(object):

    @classmethod
    @memoized
    def get_clients(cls, with_token):
        return {
            'default': DesignateClient(with_token),
            'alt': DesignateAltClient(with_token),
            'admin': DesignateAdminClient(with_token),
        }

    def __init__(self, client):
        self.client = client

    @classmethod
    def deserialize(cls, resp, body, model_type):
        return resp, model_type.from_json(body)

    @classmethod
    def as_user(cls, user, with_token=True):
        """
        :param user: 'default', 'alt', or 'admin'
        :param with_token: Boolean for whether to send the x-auth-token with
            requests
        """
        return cls(cls.get_clients(with_token)[user])

    @property
    def tenant_id(self):
        return self.client.tenant_id

    @classmethod
    def add_filters(cls, url, filters):
        """
        :param url: base URL for the request
        :param filters: dict with var:val pairs to add as parameters to URL
        """
        first = True
        for f in filters:
            if isinstance(filters[f], string_types):
                filters[f] = quote_plus(filters[f].encode('utf-8'))

            url = '{url}{sep}{var}={val}'.format(
                url=url, sep=('?' if first else '&'), var=f, val=filters[f]
            )
            first = False
        return url
