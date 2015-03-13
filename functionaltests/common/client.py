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
from tempest.auth import KeystoneV2Credentials
from tempest.config import CONF
import tempest.manager


class DesignateClient(RestClient):

    def __init__(self):
        creds = KeystoneV2Credentials(
            username=CONF.identity.admin_username,
            password=CONF.identity.admin_password,
            tenant_name=CONF.identity.admin_tenant_name,
        )
        auth_provider = tempest.manager.get_auth_provider(creds)
        auth_provider.fill_credentials()
        super(DesignateClient, self).__init__(
            auth_provider=auth_provider,
            service='dns',
            region=CONF.identity.region,
        )
