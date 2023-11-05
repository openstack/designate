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
from unittest import mock

from oslo_config import fixture as cfg_fixture
from oslo_log import log as logging
import oslotest.base

import designate.conf
from designate import exceptions
from designate import objects
from designate.objects import adapters
from designate.objects.adapters.api_v2 import base


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class APIv2AdapterTest(oslotest.base.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.useFixture(cfg_fixture.Config(CONF))

    def test_get_base_url(self):
        CONF.set_override('enable_host_header', False, 'service:api')
        CONF.set_override(
            'api_base_uri', 'http://192.0.2.1:9001/', 'service:api'
        )

        mock_request = mock.Mock()
        mock_request.GET = {'foo': 'bar'}
        mock_request.host_url = 'http://192.0.2.2'
        mock_request.path = '/v2/zones'

        base_url = base.APIv2Adapter._get_base_url(mock_request)
        self.assertEqual('http://192.0.2.1:9001', base_url)

    def test_get_base_url_enable_host_header(self):
        CONF.set_override('enable_host_header', True, 'service:api')

        mock_request = mock.Mock()
        mock_request.GET = {'foo': 'bar'}
        mock_request.host_url = 'http://192.0.2.1'
        mock_request.path = '/v2/zones'

        base_url = base.APIv2Adapter._get_base_url(mock_request)
        self.assertEqual('http://192.0.2.1', base_url)


class RecordAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_parse_object(self):
        values = '192.0.2.1'

        parsed_object = adapters.RecordAPIv2Adapter.parse_object(
            values, objects.Record()
        )

        self.assertEqual('192.0.2.1', parsed_object.data)

    def test_render_object(self):
        values = '192.0.2.1'

        parsed_object = adapters.RecordAPIv2Adapter.parse_object(
            values, objects.Record()
        )

        self.assertEqual('192.0.2.1', parsed_object.data)

        render_object = adapters.RecordAPIv2Adapter.render_object(
            parsed_object
        )

        self.assertEqual(values, render_object)


class RecordSetAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_parse_object(self):
        values = {'name': 'example.org.'}

        parsed_object = adapters.RecordSetAPIv2Adapter.parse_object(
            values, objects.RecordSet()
        )

        self.assertEqual(values['name'], parsed_object.name)

    def test_parse_object_invalid_records(self):
        values = {'name': 'example.org.', 'records': {'foo': 'bar'}}

        self.assertRaisesRegex(
            exceptions.InvalidObject,
            'Provided object does not match schema',
            adapters.RecordSetAPIv2Adapter.parse_object, values,
            objects.RecordSet()
        )

    def test_render_object(self):
        values = {'name': 'example.org.', 'records': []}

        parsed_object = adapters.RecordSetAPIv2Adapter.parse_object(
            values, objects.RecordSet()
        )

        self.assertEqual(values['name'], parsed_object.name)

        render_object = adapters.RecordSetAPIv2Adapter.render_object(
            parsed_object
        )

        self.assertIsInstance(render_object, dict)
        self.assertEqual(values['name'], parsed_object.name)

    def test_get_path(self):
        mock_request = mock.Mock()
        mock_request.path = '/v2/recordsets'
        mock_recordset = mock.Mock()
        mock_recordset.zone_id = 'a-b-c-d'
        expected_path = '/v2/zones/a-b-c-d/recordsets'

        path = adapters.RecordSetAPIv2Adapter._get_path(
            mock_request, mock_recordset
        )
        self.assertEqual(expected_path, path)


class SharedZoneAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_render_object(self):
        values = {
            'target_project_id': '60b1dd98-49a7-403b-901a-291ca555da56',
        }

        parsed_object = adapters.SharedZoneAPIv2Adapter.parse_object(
            values, objects.SharedZone()
        )

        render_object = adapters.SharedZoneAPIv2Adapter.render_object(
            parsed_object,
        )

        self.assertIsInstance(render_object, dict)
        self.assertEqual(
            '60b1dd98-49a7-403b-901a-291ca555da56',
            render_object['target_project_id']
        )

    def test_render_object_links(self):
        share_id = '9edbb487-3ca1-4e9c-9503-6dd08a04b8c2'
        zone_id = '9207ed7d-2094-4622-bce9-1af1886e958a'

        mock_request = mock.Mock()
        mock_request.host_url = 'http://192.0.2.1'
        mock_request.path = '/v2/zones/{zone_id}/shares/{zone_share_id}'
        values = {
            'target_project_id': '60b1dd98-49a7-403b-901a-291ca555da56',
        }

        parsed_object = adapters.SharedZoneAPIv2Adapter.parse_object(
            values, objects.SharedZone()
        )
        parsed_object.id = share_id
        parsed_object.zone_id = zone_id

        render_object = adapters.SharedZoneAPIv2Adapter.render_object(
            parsed_object, request=mock_request,
        )

        self.assertEqual(
            f'{mock_request.host_url}/v2/zones/{zone_id}/shares/{share_id}',
            render_object['links']['self']
        )
        self.assertEqual(
            f'{mock_request.host_url}/v2/zones/{zone_id}',
            render_object['links']['zone']
        )


class SharedZoneListAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_get_collection_href(self):
        mock_request = mock.Mock()
        mock_request.GET = {'foo': 'bar'}
        mock_request.host_url = 'http://192.0.2.1'
        mock_request.path = '/v2/zones/{zone_id}/shares'

        self.assertEqual(
            'http://192.0.2.1/v2/zones/{zone_id}/shares?foo=bar',
            adapters.SharedZoneListAPIv2Adapter._get_collection_href(
                mock_request, {}
            )
        )


class ZoneAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_parse_object(self):
        values = {
            'masters': ['192.0.2.1'],
            'attributes': {'foo': 'bar'},
        }

        adapter = adapters.ZoneAPIv2Adapter.parse_object(
            values, objects.Zone()
        )

        self.assertFalse(values)
        self.assertEqual(1, len(adapter.attributes))
        self.assertEqual('foo', adapter.attributes[0].key)
        self.assertEqual('bar', adapter.attributes[0].value)


class ZoneAttributeAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_parse_object(self):
        values = {
            'foo': 'bar'
        }

        parsed_object = adapters.ZoneAttributeAPIv2Adapter.parse_object(
            values, objects.ZoneAttribute()
        )

        self.assertEqual('foo', parsed_object.key)
        self.assertEqual('bar', parsed_object.value)

    def test_render_object(self):
        values = {
            'foo': 'bar'
        }

        parsed_object = adapters.ZoneAttributeAPIv2Adapter.parse_object(
            values, objects.ZoneAttribute()
        )

        self.assertEqual('foo', parsed_object.key)
        self.assertEqual('bar', parsed_object.value)

        render_object = adapters.ZoneAttributeAPIv2Adapter.render_object(
            parsed_object
        )

        self.assertIsInstance(render_object, dict)
        self.assertEqual(values, render_object)


class ZoneAttributeListAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_parse_list(self):
        zone_attribute = objects.ZoneAttribute(key='foo', value='bar')

        parsed_object = adapters.ZoneAttributeListAPIv2Adapter.parse_object(
            {}, objects.ZoneAttributeList(objects=[zone_attribute])
        )

        self.assertEqual(1, len(parsed_object))

    def test_render_list(self):
        zone_attribute = objects.ZoneAttribute(key='foo', value='bar')

        parsed_object = adapters.ZoneAttributeListAPIv2Adapter.parse_object(
            {}, objects.ZoneAttributeList(objects=[zone_attribute])
        )

        self.assertEqual(1, len(parsed_object))

        render_object = adapters.ZoneAttributeListAPIv2Adapter.render_list(
            parsed_object
        )

        self.assertEqual({'foo': 'bar'}, render_object)


class ZoneExportAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_render_object_links(self):
        export_id = '51790877-ddb7-4351-b3af-23fb6e53098b'

        mock_request = mock.Mock()
        mock_request.GET = {'foo': 'bar'}
        mock_request.host_url = 'designate://192.0.2.1'
        mock_request.path = '/v2/zones/{zone_id}/tasks/export'

        parsed_object = adapters.ZoneExportAPIv2Adapter.parse_object(
            {}, objects.ZoneExport()
        )
        parsed_object.location = (
            'designate://192.0.2.1/v2/zones/{zone_id}/tasks/export'
        )
        parsed_object.id = export_id
        render_object = adapters.ZoneExportAPIv2Adapter.render_object(
            parsed_object, request=mock_request,
        )

        self.assertEqual(
            'designate://192.0.2.1/192.0.2.1/v2/zones/{zone_id}/tasks/export',
            render_object['links']['export']
        )
        self.assertEqual(
            f'designate://192.0.2.1/v2/zones/tasks/exports/{export_id}',
            render_object['links']['self']
        )


class ZoneMasterAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_parse_object(self):
        value = '192.0.2.1:5353'

        parsed_object = adapters.ZoneMasterAPIv2Adapter.parse_object(
            value, objects.ZoneMaster()
        )

        self.assertEqual('192.0.2.1', parsed_object.host)
        self.assertEqual(5353, parsed_object.port)

    def test_render_object(self):
        value = '192.0.2.1:5353'

        parsed_object = adapters.ZoneMasterAPIv2Adapter.parse_object(
            value, objects.ZoneMaster()
        )

        self.assertEqual('192.0.2.1', parsed_object.host)
        self.assertEqual(5353, parsed_object.port)

        render_object = adapters.ZoneMasterAPIv2Adapter.render_object(
            parsed_object
        )

        self.assertEqual('192.0.2.1:5353', render_object)

    def test_render_object_standard_dns_port(self):
        value = '192.0.2.1:53'

        parsed_object = adapters.ZoneMasterAPIv2Adapter.parse_object(
            value, objects.ZoneMaster()
        )

        self.assertEqual('192.0.2.1', parsed_object.host)
        self.assertEqual(53, parsed_object.port)

        render_object = adapters.ZoneMasterAPIv2Adapter.render_object(
            parsed_object
        )

        self.assertEqual('192.0.2.1', render_object)


class ZoneTransferRequestAPIv2AdapterTest(oslotest.base.BaseTestCase):
    def test_parse_object(self):
        values = {
            'target_project_id': '60b1dd98-49a7-403b-901a-291ca555da56',
        }

        parsed_object = adapters.ZoneTransferRequestAPIv2Adapter.parse_object(
            values, objects.ZoneTransferRequest()
        )

        self.assertEqual(
            '60b1dd98-49a7-403b-901a-291ca555da56',
            parsed_object.target_tenant_id
        )

    @mock.patch('designate.policy.check', mock.Mock())
    def test_render_object(self):
        mock_context = mock.Mock()
        values = {
            'target_project_id': '60b1dd98-49a7-403b-901a-291ca555da56',
        }

        parsed_object = adapters.ZoneTransferRequestAPIv2Adapter.parse_object(
            values, objects.ZoneTransferRequest()
        )

        self.assertEqual(
            '60b1dd98-49a7-403b-901a-291ca555da56',
            parsed_object.target_tenant_id
        )

        render_object = adapters.ZoneTransferRequestAPIv2Adapter.render_object(
            parsed_object, context=mock_context
        )

        self.assertEqual(
            '60b1dd98-49a7-403b-901a-291ca555da56',
            render_object['target_project_id']
        )

    @mock.patch('designate.policy.check')
    def test_render_object_forbidden_raised(self, mock_policy_check):
        mock_policy_check.side_effect = exceptions.Forbidden()
        mock_context = mock.Mock()
        values = {
            'target_project_id': '60b1dd98-49a7-403b-901a-291ca555da56',
        }

        parsed_object = adapters.ZoneTransferRequestAPIv2Adapter.parse_object(
            values, objects.ZoneTransferRequest()
        )

        self.assertEqual(
            '60b1dd98-49a7-403b-901a-291ca555da56',
            parsed_object.target_tenant_id
        )

        render_object = adapters.ZoneTransferRequestAPIv2Adapter.render_object(
            parsed_object, context=mock_context
        )

        self.assertNotIn('target_project_id', render_object)
