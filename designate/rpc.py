# Copyright 2013 Red Hat, Inc.
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
import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher as rpc_dispatcher
from oslo_serialization import jsonutils
from oslo_utils import importutils

import designate.conf
import designate.context
import designate.exceptions
from designate import objects


profiler = importutils.try_import('osprofiler.profiler')

__all__ = [
    'init',
    'cleanup',
    'set_defaults',
    'add_extra_exmods',
    'clear_extra_exmods',
    'get_allowed_exmods',
    'RequestContextSerializer',
    'get_client',
    'get_server',
    'get_notifier',
]

CONF = designate.conf.CONF
NOTIFICATION_TRANSPORT = None
NOTIFIER = None
TRANSPORT = None

# NOTE: Additional entries to designate.exceptions goes here.
ALLOWED_EXMODS = [
    designate.exceptions.__name__,
    'designate.backend.impl_dynect'
]
EXTRA_EXMODS = []


def init(conf):
    global TRANSPORT, NOTIFIER, NOTIFICATION_TRANSPORT
    exmods = get_allowed_exmods()
    TRANSPORT = create_transport(get_transport_url())
    NOTIFICATION_TRANSPORT = messaging.get_notification_transport(
        conf, allowed_remote_exmods=exmods)
    serializer = RequestContextSerializer(JsonPayloadSerializer())
    NOTIFIER = messaging.Notifier(NOTIFICATION_TRANSPORT,
                                  serializer=serializer)


def initialized():
    return None not in [TRANSPORT, NOTIFIER, NOTIFICATION_TRANSPORT]


def cleanup():
    global TRANSPORT, NOTIFIER, NOTIFICATION_TRANSPORT
    if TRANSPORT is None:
        raise AssertionError("'TRANSPORT' must not be None")
    if NOTIFICATION_TRANSPORT is None:
        raise AssertionError("'NOTIFICATION_TRANSPORT' must not be None")
    if NOTIFIER is None:
        raise AssertionError("'NOTIFIER' must not be None")
    TRANSPORT.cleanup()
    NOTIFICATION_TRANSPORT.cleanup()
    TRANSPORT = NOTIFICATION_TRANSPORT = NOTIFIER = None


def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)


def add_extra_exmods(*args):
    EXTRA_EXMODS.extend(args)


def clear_extra_exmods():
    del EXTRA_EXMODS[:]


def get_allowed_exmods():
    return ALLOWED_EXMODS + EXTRA_EXMODS + CONF.allowed_remote_exmods


class JsonPayloadSerializer(messaging.NoOpSerializer):
    @staticmethod
    def serialize_entity(context, entity):
        return jsonutils.to_primitive(entity, convert_instances=True)


class DesignateObjectSerializer(messaging.NoOpSerializer):
    def _process_iterable(self, context, action_fn, values):
        """Process an iterable, taking an action on each value.
        :param:context: Request context
        :param:action_fn: Action to take on each item in values
        :param:values: Iterable container of things to take action on
        :returns: A new container of the same type (except set) with
        items from values having had action applied.
        """
        iterable = values.__class__
        if iterable == set:
            # NOTE: A set can't have an unhashable value inside, such as
            # a dict. Convert sets to tuples, which is fine, since we can't
            # send them over RPC anyway.
            iterable = tuple
        return iterable([action_fn(context, value) for value in values])

    def serialize_entity(self, context, entity):
        if isinstance(entity, (tuple, list, set)):
            entity = self._process_iterable(context, self.serialize_entity,
                                            entity)
        elif hasattr(entity, 'to_primitive') and callable(entity.to_primitive):
            entity = entity.to_primitive()

        return jsonutils.to_primitive(entity, convert_instances=True)

    def deserialize_entity(self, context, entity):
        if isinstance(entity, dict) and 'designate_object.name' in entity:
            entity = objects.DesignateObject.from_primitive(entity)
        elif isinstance(entity, (tuple, list, set)):
            entity = self._process_iterable(context, self.deserialize_entity,
                                            entity)
        return entity


class RequestContextSerializer(messaging.Serializer):

    def __init__(self, base):
        self._base = base

    def serialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(context, entity)

    def deserialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(context, entity)

    def serialize_context(self, context):
        _context = context.to_dict()
        if profiler is not None:
            prof = profiler.get()
            if prof is not None:
                trace_info = {
                    "hmac_key": prof.hmac_key,
                    "base_id": prof.get_base_id(),
                    "parent_id": prof.get_id()
                }
                _context.update({"trace_info": trace_info})
        return _context

    def deserialize_context(self, context):
        trace_info = context.pop("trace_info", None)
        if trace_info is not None and profiler is not None:
            profiler.init(**trace_info)
        return designate.context.DesignateContext.from_dict(context)


def get_transport_url(url_str=None):
    return messaging.TransportURL.parse(CONF, url_str)


def get_client(target, version_cap=None, serializer=None):
    if TRANSPORT is None:
        raise AssertionError("'TRANSPORT' must not be None")
    if serializer is None:
        serializer = DesignateObjectSerializer()
    serializer = RequestContextSerializer(serializer)
    return messaging.get_rpc_client(
        TRANSPORT,
        target,
        version_cap=version_cap,
        serializer=serializer
    )


def get_server(target, endpoints, serializer=None):
    if TRANSPORT is None:
        raise AssertionError("'TRANSPORT' must not be None")
    if serializer is None:
        serializer = DesignateObjectSerializer()
    serializer = RequestContextSerializer(serializer)
    access_policy = rpc_dispatcher.DefaultRPCAccessPolicy
    return messaging.get_rpc_server(
        TRANSPORT,
        target,
        endpoints,
        executor='eventlet',
        serializer=serializer,
        access_policy=access_policy
    )


def get_notification_listener(targets, endpoints, serializer=None, pool=None):
    if NOTIFICATION_TRANSPORT is None:
        raise AssertionError("'NOTIFICATION_TRANSPORT' must not be None")
    if serializer is None:
        serializer = JsonPayloadSerializer()
    return messaging.get_notification_listener(
        NOTIFICATION_TRANSPORT,
        targets,
        endpoints,
        executor='eventlet',
        pool=pool,
        serializer=serializer
    )


def get_notifier(service=None, host=None, publisher_id=None):
    if NOTIFIER is None:
        raise AssertionError("'NOTIFIER' must not be None")
    if not publisher_id:
        publisher_id = f'{service}.{host or CONF.host}'
    return NOTIFIER.prepare(publisher_id=publisher_id)


def create_transport(url):
    exmods = get_allowed_exmods()
    return messaging.get_rpc_transport(CONF,
                                       url=url,
                                       allowed_remote_exmods=exmods)
