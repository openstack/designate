# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest import clients
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
import tempest.test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseDnsTest(tempest.test.BaseTestCase):
    """Base test case class for all Dns API tests."""

    _interface = 'json'
    force_tenant_isolation = False

    @classmethod
    def setUpClass(cls):
        super(BaseDnsTest, cls).setUpClass()
        if not CONF.service_available.designate:
            skip_msg = ("%s skipped as designate is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)
        os = cls.get_client_manager()
        cls.os = os
        cls.dns_domains_client = cls.os.dns_domains_client
        cls.dns_records_client = cls.os.dns_records_client


class BaseDnsAdminTest(BaseDnsTest):
    """Base test case class for Dns Admin API tests."""
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(BaseDnsAdminTest, cls).setUpClass()
        if (CONF.compute.allow_tenant_isolation or
                cls.force_tenant_isolation is True):
            creds = cls.isolated_creds.get_admin_creds()
            cls.os_adm = clients.Manager(credentials=creds,
                                         interface=cls._interface)
        else:
            try:
                cls.os_adm = clients.DnsAdminManager(
                    interface=cls._interface)
            except exceptions.InvalidCredentials:
                msg = ("Missing Dns Admin API credentials "
                       "in configuration.")
                raise cls.skipException(msg)
