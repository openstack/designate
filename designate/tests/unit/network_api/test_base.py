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
# under the License.mport threading
from oslo_config import fixture as cfg_fixture
import oslotest.base

import designate.conf
import designate.exceptions
from designate.network_api import base


CONF = designate.conf.CONF

SERVICE_CATALOG = [
    {
        'endpoints': [
            {
                'adminURL': 'admin1',
                'region': 'RegionOne',
                'internalURL': 'internal1',
                'publicURL': 'public1'
            }
        ],
        'type': 'dns',
        'name': 'foo1'
    },
    {
        'endpoints': [
            {
                'adminURL': 'admin2',
                'region': 'RegionTwo',
                'internalURL': 'internal2',
                'publicURL': 'public2'
            }
        ],
        'type': 'dns',
        'name': 'foo2'
    },
    {
        'endpoints': [
            {
                'adminURL': 'admin3',
                'region': 'RegionTwo',
                'internalURL': 'internal3',
                'publicURL': 'public3'
            }
        ],
        'type': 'network',
        'name': 'foo2'
    },
]


class NetworkEndpointsTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.base = base.NetworkAPI()

    def test_endpoints_from_config(self):
        CONF.set_override(
            'endpoints', ['RegionThree|public3', 'RegionFour|public4'],
            'network_api:neutron'
        )

        result = self.base._endpoints(
            service_catalog=SERVICE_CATALOG,
            service_type='dns',
            endpoint_type='publicURL',
            config_section='network_api:neutron',
        )

        self.assertEqual(
            [('public3', 'RegionThree'), ('public4', 'RegionFour')], result
        )

    def test_endpoints_from_config_with_region(self):
        CONF.set_override(
            'endpoints', ['RegionThree|public3', 'RegionFour|public4'],
            'network_api:neutron'
        )

        result = self.base._endpoints(
            service_catalog=SERVICE_CATALOG,
            service_type='dns',
            endpoint_type='publicURL',
            region='RegionFour',
            config_section='network_api:neutron',
        )

        self.assertEqual(
            [('public4', 'RegionFour')], result
        )

    def test_endpoints_from_catalog(self):
        result = self.base._endpoints(
            service_catalog=SERVICE_CATALOG,
            service_type='dns',
            endpoint_type='publicURL',
            config_section='network_api:neutron',
        )

        self.assertEqual(
            [('public1', 'RegionOne'), ('public2', 'RegionTwo')], result
        )

    def test_endpoints_from_catalog_with_region(self):
        result = self.base._endpoints(
            service_catalog=SERVICE_CATALOG,
            service_type='dns',
            endpoint_type='publicURL',
            region='RegionOne',
            config_section='network_api:neutron',
        )

        self.assertEqual(
            [('public1', 'RegionOne')], result
        )

    def test_no_endpoints_or_service_catalog_available(self):
        self.assertRaisesRegex(
            designate.exceptions.ConfigurationError,
            'No service_catalog and no configured endpoints',
            self.base._endpoints,
            service_catalog=None,
            service_type='dns',
            endpoint_type='publicURL',
            config_section='network_api:neutron',
        )


class NetworkEndpointsFromConfigTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

        self.base = base.NetworkAPI()

    def test_endpoint(self):
        CONF.set_override(
            'endpoints', ['RegionThree|public3'], 'network_api:neutron'
        )

        result = self.base.endpoints_from_config(
            CONF['network_api:neutron'].endpoints,
        )

        self.assertEqual(
            [('public3', 'RegionThree')], result
        )

    def test_endpoints(self):
        CONF.set_override(
            'endpoints', ['RegionThree|public3', 'RegionFour|public4'],
            'network_api:neutron'
        )

        result = self.base.endpoints_from_config(
            CONF['network_api:neutron'].endpoints,
        )

        self.assertEqual(
            [('public3', 'RegionThree'), ('public4', 'RegionFour')], result
        )

    def test_endpoint_from_region(self):
        CONF.set_override(
            'endpoints', ['RegionThree|public3', 'RegionFour|public4'],
            'network_api:neutron'
        )

        result = self.base.endpoints_from_config(
            CONF['network_api:neutron'].endpoints,
            region='RegionFour',
        )

        self.assertEqual(
            [('public4', 'RegionFour')], result
        )

    def test_endpoint_from_region_not_found(self):
        CONF.set_override(
            'endpoints', ['RegionThree|public3', 'RegionThree|public4'],
            'network_api:neutron'
        )

        self.assertRaisesRegex(
            designate.exceptions.ConfigurationError,
            'Endpoints are not correctly configured',
            self.base.endpoints_from_config,
            CONF['network_api:neutron'].endpoints,
            region='RegionFive',
        )

    def test_endpoint_empty_list(self):
        CONF.set_override(
            'endpoints', [],
            'network_api:neutron'
        )

        self.assertRaisesRegex(
            designate.exceptions.ConfigurationError,
            'Endpoints are not correctly configured',
            self.base.endpoints_from_config,
            CONF['network_api:neutron'].endpoints,
        )


class NetworkEndpointsFromCatalogTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()

        self.base = base.NetworkAPI()

    def test_endpoints(self):
        result = self.base.endpoints_from_catalog(
            service_catalog=SERVICE_CATALOG,
            service_type='dns',
            endpoint_type='publicURL',
        )

        self.assertEqual(
            [('public1', 'RegionOne'), ('public2', 'RegionTwo')], result
        )

    def test_endpoint_from_region(self):
        result = self.base.endpoints_from_catalog(
            service_catalog=SERVICE_CATALOG,
            service_type='dns',
            endpoint_type='publicURL',
            region='RegionTwo',
        )

        self.assertEqual(
            [('public2', 'RegionTwo')], result
        )

    def test_endpoint_region_not_found(self):
        self.assertRaises(
            designate.exceptions.NetworkEndpointNotFound,
            self.base.endpoints_from_catalog,
            service_type='dns',
            endpoint_type='publicURL',
            region='RegionSix',
            service_catalog=SERVICE_CATALOG,
        )

    def test_no_endpoints_found(self):
        self.assertRaises(
            designate.exceptions.NetworkEndpointNotFound,
            self.base.endpoints_from_catalog,
            service_type='compute',
            endpoint_type='publicURL',
            service_catalog=SERVICE_CATALOG,
        )
