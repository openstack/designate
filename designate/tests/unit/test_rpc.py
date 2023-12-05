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

import oslo_messaging as messaging
import oslotest.base

import designate.conf
from designate import rpc

CONF = designate.conf.CONF


def action_test(a, b):
    return f'{a}-{b}'


class DesignateObjectSerializerTest(oslotest.base.BaseTestCase):
    def test_process_iterable(self):
        context = 'context'
        values = ['foo', 'bar']

        serializer = rpc.DesignateObjectSerializer()
        self.assertEqual(
            ['context-bar', 'context-foo'],
            sorted(serializer._process_iterable(context, action_test, values))
        )

    def test_process_iterable_with_set(self):
        context = 'context'
        values = {'foo', 'bar'}

        serializer = rpc.DesignateObjectSerializer()
        self.assertEqual(
            ('context-bar', 'context-foo'),
            tuple(sorted(
                serializer._process_iterable(context, action_test, values))
            )
        )


class RequestContextSerializerTest(oslotest.base.BaseTestCase):
    def test_serialize_entity_base_not_set(self):
        entity = 'entity'

        request = rpc.RequestContextSerializer(None)
        self.assertEqual(entity, request.serialize_entity(None, entity))

    def test_deserialize_entity_base_not_set(self):
        entity = 'entity'

        request = rpc.RequestContextSerializer(None)
        self.assertEqual(entity, request.deserialize_entity(None, entity))

    @mock.patch.object(rpc, 'profiler', mock.Mock())
    def test_serialize_context_with_profiler(self):
        mock_context = mock.Mock()
        mock_context.to_dict.return_value = {}
        request = rpc.RequestContextSerializer(None)

        self.assertIn('trace_info', request.serialize_context(mock_context))

    @mock.patch.object(rpc, 'profiler', None)
    def test_serialize_context_without_profiler(self):
        mock_context = mock.Mock()
        mock_context.to_dict.return_value = {}
        request = rpc.RequestContextSerializer(None)

        self.assertNotIn('trace_info', request.serialize_context(mock_context))

    @mock.patch.object(rpc, 'profiler')
    @mock.patch('designate.context.DesignateContext.from_dict', mock.Mock())
    def test_deserialize_context_with_profiler(self, mock_profile):
        mock_context = mock.Mock()
        mock_context.pop.return_value = {'key': 'value'}
        request = rpc.RequestContextSerializer(None)

        request.deserialize_context(mock_context)

        mock_profile.init.assert_called_with(key='value')

    @mock.patch.object(rpc, 'profiler')
    @mock.patch('designate.context.DesignateContext.from_dict', mock.Mock())
    def test_deserialize_context_without_trace_info(self, mock_profile):
        mock_context = mock.Mock()
        mock_context.pop.return_value = None
        request = rpc.RequestContextSerializer(None)

        request.deserialize_context(mock_context)

        mock_profile.init.assert_not_called()


class RPCTest(oslotest.base.BaseTestCase):
    @mock.patch.object(designate.rpc, 'NOTIFIER', mock.Mock())
    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT')
    @mock.patch.object(designate.rpc, 'TRANSPORT')
    def test_cleanup(self, mock_transport, mock_notification_transport):
        self.assertTrue(rpc.TRANSPORT)
        self.assertTrue(rpc.NOTIFICATION_TRANSPORT)
        self.assertTrue(rpc.NOTIFIER)

        rpc.cleanup()

        mock_transport.cleanup.assert_called_once()
        mock_notification_transport.cleanup.assert_called_once()

        self.assertIsNone(rpc.TRANSPORT)
        self.assertIsNone(rpc.NOTIFICATION_TRANSPORT)
        self.assertIsNone(rpc.NOTIFIER)

    @mock.patch.object(designate.rpc, 'NOTIFIER', True)
    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', True)
    @mock.patch.object(designate.rpc, 'TRANSPORT', None)
    def test_cleanup_no_transport(self):
        self.assertRaisesRegex(
            AssertionError,
            r"'TRANSPORT' must not be None",
            rpc.cleanup
        )

    @mock.patch.object(designate.rpc, 'NOTIFIER', True)
    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', None)
    @mock.patch.object(designate.rpc, 'TRANSPORT', True)
    def test_cleanup_no_notification_transport(self):
        self.assertRaisesRegex(
            AssertionError,
            r"'NOTIFICATION_TRANSPORT' must not be None",
            rpc.cleanup
        )

    @mock.patch.object(designate.rpc, 'NOTIFIER', None)
    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', True)
    @mock.patch.object(designate.rpc, 'TRANSPORT', True)
    def test_cleanup_no_notifier(self):
        self.assertRaisesRegex(
            AssertionError,
            r"'NOTIFIER' must not be None",
            rpc.cleanup
        )

    def test_add_extra_exmods(self):
        rpc.add_extra_exmods('arg1', 'arg2', 'arg3')
        self.assertEqual(['arg1', 'arg2', 'arg3'], rpc.EXTRA_EXMODS)

        rpc.clear_extra_exmods()

    def test_clear_extra_exmods(self):
        rpc.add_extra_exmods('arg1', 'arg2', 'arg3')
        rpc.clear_extra_exmods()

        self.assertEqual([], rpc.EXTRA_EXMODS)

    @mock.patch.object(messaging, 'set_transport_defaults')
    def test_set_defaults(self, mock_set_transport_defaults):
        rpc.set_defaults('test')

        mock_set_transport_defaults.assert_called_with('test')

    @mock.patch.object(designate.rpc, 'NOTIFIER', True)
    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', True)
    @mock.patch.object(designate.rpc, 'TRANSPORT', True)
    @mock.patch.object(messaging, 'get_rpc_server')
    def test_get_server(self, mock_get_rpc_server):
        rpc.get_server(None, None, True)

        mock_get_rpc_server.assert_called_with(
            True, None, None,
            executor='eventlet', serializer=mock.ANY,
            access_policy=mock.ANY,
        )

    @mock.patch.object(designate.rpc, 'TRANSPORT', None)
    def test_get_server_transport_is_none(self):
        self.assertRaisesRegex(
            AssertionError,
            r"'TRANSPORT' must not be None",
            rpc.get_server, None, None
        )

    @mock.patch.object(designate.rpc, 'TRANSPORT', True)
    @mock.patch.object(messaging, 'get_rpc_client')
    def test_get_client(self, mock_get_rpc_client):
        rpc.get_client(None, None, True)

        mock_get_rpc_client.assert_called_with(
            True, None,
            version_cap=None, serializer=mock.ANY,
        )

    @mock.patch.object(designate.rpc, 'TRANSPORT', None)
    def test_get_client_is_none(self):
        self.assertRaisesRegex(
            AssertionError,
            r"'TRANSPORT' must not be None",
            rpc.get_client, None, None
        )

    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', True)
    @mock.patch.object(messaging, 'get_notification_listener')
    def test_get_notification_listener(self, mock_get_notification_listener):
        rpc.get_notification_listener('target', 'endpoint', serializer=None)

        mock_get_notification_listener.assert_called_with(
            True, 'target', 'endpoint', executor='eventlet', pool=None,
            serializer=mock.ANY
        )

    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', True)
    @mock.patch.object(messaging, 'get_notification_listener')
    def test_get_notification_listener_serializer_set(self,
                                             mock_get_notification_listener):
        rpc.get_notification_listener('target', 'endpoint', serializer=True)

        mock_get_notification_listener.assert_called_with(
            True, 'target', 'endpoint', executor='eventlet', pool=None,
            serializer=True
        )

    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', None)
    def test_get_notification_listener_transport_is_none(self):
        self.assertRaisesRegex(
            AssertionError,
            r"'NOTIFICATION_TRANSPORT' must not be None",
            rpc.get_notification_listener, None, None
        )

    @mock.patch.object(designate.rpc, 'NOTIFIER', None)
    @mock.patch.object(designate.rpc, 'NOTIFICATION_TRANSPORT', None)
    @mock.patch.object(designate.rpc, 'TRANSPORT', None)
    @mock.patch('oslo_messaging.notify.notifier.Notifier.prepare')
    def test_get_notifier(self, mock_prepare):
        rpc.init(CONF)

        rpc.get_notifier(publisher_id=True)

        mock_prepare.assert_called_with(publisher_id=True)

    @mock.patch.object(designate.rpc, 'NOTIFIER', None)
    def test_get_notifier_is_none(self):
        self.assertRaisesRegex(
            AssertionError,
            r"'NOTIFIER' must not be None",
            rpc.get_notifier
        )
