# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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

import mock

from designate.tests import TestCase
from designate import exceptions

from oslo_config import cfg
from oslo_config import fixture as cfg_fixture

from designate.objects.adapters.api_v2 import base


class MockRequest(object):

    def __init__(self, GET=None):
        self.GET = GET


class TestAPIv2(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf

    @mock.patch.object(base.APIv2Adapter, '_get_collection_href')
    @mock.patch.object(base.APIv2Adapter, '_get_next_href')
    def test_limit_max(self, mock_coll_href, mock_next_href):
        # Bug 1494799 bug:1494799
        mock_coll_href.return_value = None
        mock_next_href.return_value = None
        item_list = range(200)
        request = MockRequest(GET=dict(limit="max"))
        links = base.APIv2Adapter._get_collection_links(item_list, request)
        self.assertEqual(links, dict(self=None))

        request = MockRequest(GET=dict(limit="MAX"))
        links = base.APIv2Adapter._get_collection_links(item_list, request)
        self.assertEqual(links, dict(self=None))

        request = MockRequest(GET=dict(limit="200"))
        links = base.APIv2Adapter._get_collection_links(item_list, request)
        self.assertEqual(links, dict(self=None, next=None))

        request = MockRequest(GET=dict(limit="BOGUS_STRING"))
        self.assertRaises(
            exceptions.ValueError,
            base.APIv2Adapter._get_collection_links, item_list, request
        )
