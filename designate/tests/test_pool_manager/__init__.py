# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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

from designate.tests import TestCase
from designate.utils import DEFAULT_MDNS_PORT

POOL_DICT = {
    'id': u'794ccc2c-d751-44fe-b57f-8894c9f5c842',
    'name': u'default',
    'targets': [
        {
            'id': 'f278782a-07dc-4502-9177-b5d85c5f7c7e',
            'type': 'fake',
            'masters': [
                {
                    'host': '127.0.0.1',
                    'port': DEFAULT_MDNS_PORT
                }
            ],
            'options': {}
        },
        {
            'id': 'a38703f2-b71e-4e5b-ab22-30caaed61dfd',
            'type': 'fake',
            'masters': [
                {
                    'host': '127.0.0.1',
                    'port': DEFAULT_MDNS_PORT
                }
            ],
            'options': {}
        },
    ],
    'nameservers': [
        {
            'id': 'c5d64303-4cba-425a-9f3c-5d708584dde4',
            'host': '127.0.0.1',
            'port': 5355

        },
        {
            'id': 'c67cdc95-9a9e-4d2a-98ed-dc78cbd85234',
            'host': '127.0.0.1',
            'port': 5356
        },
    ],
    'also_notifies': [],
}


class PoolManagerTestCase(TestCase):
    pass
