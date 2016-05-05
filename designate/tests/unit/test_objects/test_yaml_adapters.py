# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import os

import yaml
from oslo_log import log as logging
import oslotest.base

from designate import objects
from designate.objects import adapters
from designate.tests import resources
from designate.utils import DEFAULT_MDNS_PORT


LOG = logging.getLogger(__name__)


class DesignateYAMLAdapterTest(oslotest.base.BaseTestCase):

    def assertNestedDictContainsSubset(self, expected, actual):
        for key, value in expected.items():
            if isinstance(value, dict):
                self.assertNestedDictContainsSubset(value, actual.get(key, {}))

            elif isinstance(value, list):
                self.assertEqual(len(value), len(actual[key]))

                for index, item in enumerate(value):
                    self.assertNestedDictContainsSubset(
                        item, actual[key][index])

            else:
                self.assertEqual(value, actual[key])

    def test_yaml_parsing(self):

        file = os.path.join(resources.path, 'pools_yaml/pools.yaml')
        with open(file, 'r') as stream:
            xpools = yaml.safe_load(stream)

        for xpool in xpools:
            r_pool = adapters.DesignateAdapter.parse(
                'YAML', xpool, objects.Pool())
            self.assertEqual('default', r_pool.name)
            self.assertEqual('Default PowerDNS Pool', r_pool.description)
            self.assertEqual(2, len(r_pool.ns_records))
            self.assertEqual(1, r_pool.ns_records[0].priority)
            self.assertEqual(2, r_pool.ns_records[1].priority)
            self.assertEqual(
                'ns1-1.example.org.', r_pool.ns_records[0].hostname)
            self.assertEqual(
                'ns1-2.example.org.', r_pool.ns_records[1].hostname)
            self.assertEqual(1, len(r_pool.targets))
            self.assertEqual('powerdns', r_pool.targets[0].type)
            self.assertEqual(
                'PowerDNS Database Cluster', r_pool.targets[0].description)
            self.assertEqual(1, len(r_pool.targets[0].masters))
            self.assertEqual('192.0.2.1', r_pool.targets[0].masters[0].host)
            self.assertEqual(DEFAULT_MDNS_PORT,
                             r_pool.targets[0].masters[0].port)
            self.assertEqual(1, len(r_pool.targets[0].options))
            self.assertEqual('connection', r_pool.targets[0].options[0].key)
            self.assertEqual(
                'mysql+pymysql://designate:password@127.0.0.1/designate_pdns?charset=utf8',  # noqa
                r_pool.targets[0].options[0].value)
            self.assertEqual(1, len(r_pool.also_notifies))
            self.assertEqual('192.0.2.4', r_pool.also_notifies[0].host)
            self.assertEqual(53, r_pool.also_notifies[0].port)
            self.assertEqual(1, len(r_pool.attributes))
            self.assertEqual('type', r_pool.attributes[0].key)
            self.assertEqual('internal', r_pool.attributes[0].value)

    def test_yaml_rendering(self):

        pool_dict = {
            'also_notifies': [
                {
                    'host': u'192.0.2.4',
                    'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
                    'port': 53,
                }
            ],
            'attributes': [],
            'description': u'Default PowerDNS Pool',
            'id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
            'name': u'default',
            'nameservers': [
                {
                    'host': u'192.0.2.2',
                    'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
                    'port': 53,
                },
                {
                    'host': u'192.0.2.3',
                    'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
                    'port': 53,
                }
            ],
            'ns_records': [
                {
                    'hostname': u'ns1-1.example.org.',
                    'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
                    'priority': 1,
                },
                {
                    'hostname': u'ns1-2.example.org.',
                    'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
                    'priority': 2,
                }
            ],
            'provisioner': u'UNMANAGED',
            'targets': [
                {
                    'description': u'PowerDNS Database Cluster',
                    'masters': [
                        {
                            'host': u'192.0.2.1',
                            'pool_target_id': u'd567d569-2d69-41d5-828d-f7054bb10b5c',  # noqa
                            'port': DEFAULT_MDNS_PORT,
                        }
                    ],
                    'options': [
                        {
                            'key': u'connection',
                            'pool_target_id': u'd567d569-2d69-41d5-828d-f7054bb10b5c',  # noqa
                            'value': u'mysql+pymysql://designate:password@127.0.0.1/designate_pdns?charset=utf8',  # noqa
                        }
                    ],
                    'pool_id': u'cf2e8eab-76cd-4162-bf76-8aeee3556de0',
                    'type': u'powerdns',
                }
            ]
        }

        file = os.path.join(resources.path, 'pools_yaml/sample_output.yaml')
        with open(file, 'r') as stream:
            self.assertEqual(
                stream.read(),
                yaml.dump(
                    adapters.DesignateAdapter.render(
                        'YAML', objects.PoolList.from_list([pool_dict])
                    ),
                    default_flow_style=False
                )
            )
