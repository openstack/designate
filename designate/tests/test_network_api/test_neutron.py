# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
from neutronclient.v2_0 import client as clientv20
from neutronclient.common import exceptions as neutron_exceptions
from oslo_config import cfg
from mock import patch
import testtools

from designate import exceptions
from designate.network_api import get_network_api
from designate.tests import TestCase


cfg.CONF.import_group('network_api:neutron', 'designate.network_api.neutron')


class NeutronAPITest(TestCase):
    def setUp(self):
        super(NeutronAPITest, self).setUp()
        self.config(endpoints=['RegionOne|http://localhost:9696'],
                    group='network_api:neutron')
        self.api = get_network_api('neutron')

    @patch.object(clientv20.Client, 'list_floatingips',
                  side_effect=neutron_exceptions.Unauthorized)
    def test_unauthorized_returns_empty(self, _):
        context = self.get_context(tenant='a', auth_token='test')

        fips = self.api.list_floatingips(context)
        self.assertEqual(0, len(fips))

    @patch.object(clientv20.Client, 'list_floatingips',
                  side_effect=neutron_exceptions.NeutronException)
    def test_communication_failure(self, _):
        context = self.get_context(tenant='a', auth_token='test')

        with testtools.ExpectedException(
                exceptions.NeutronCommunicationFailure):
            self.api.list_floatingips(context)
