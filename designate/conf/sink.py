# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
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
from oslo_config import cfg

SINK_GROUP = cfg.OptGroup(
    name='service:sink',
    title="Configuration for Sink Service"
)

SINK_FAKE_GROUP = cfg.OptGroup(
    name='handler:fake',
    title="Configuration for the Fake Notification Handler"
)

SINK_NEUTRON_GROUP = cfg.OptGroup(
    name='handler:neutron_floatingip',
    title="Configuration for Neutron Notification Handler"
)

SINK_NOVA_GROUP = cfg.OptGroup(
    name='handler:nova_fixed',
    title="Configuration for Nova Notification Handler"
)

SINK_OPTS = [
    cfg.IntOpt('workers',
               help='Number of sink worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of sink greenthreads to spawn'),
    cfg.ListOpt('enabled_notification_handlers', default=[],
                help='Enabled Notification Handlers'),
    cfg.StrOpt('listener_pool_name',
               help='pool name to use for oslo.messaging '
                    'notification listener. '
                    'Note that listener pooling is not supported '
                    'by all oslo.messaging drivers.'),
]

SINK_FAKE_OPTS = [
    cfg.ListOpt('notification_topics', default=['notifications'],
                help='notification events for the fake notification handler'),
    cfg.StrOpt('control_exchange', default='fake',
               help='control-exchange for fake notifications'),
    cfg.ListOpt('allowed_event_types', default=[],
                help='the event types we want the fake handler to accept'),
]

SINK_NEUTRON_OPTS = [
    cfg.ListOpt('notification_topics', default=['notifications'],
                help='notification any events from neutron'),
    cfg.StrOpt('control_exchange', default='neutron',
               help='control-exchange for neutron notification'),
    cfg.StrOpt('zone_id', help='Zone ID with each notification'),
    cfg.MultiStrOpt('formatv4', help='IPv4 format'),
    cfg.MultiStrOpt('format', deprecated_for_removal=True,
                    deprecated_reason="Replaced by 'formatv4/formatv6'",
                    help='format which replaced by formatv4/formatv6'),
    cfg.MultiStrOpt('formatv6', help='IPv6 format'),
]

SINK_NOVA_OPTS = [
    cfg.ListOpt('notification_topics', default=['notifications'],
                help='notification any events from nova'),
    cfg.StrOpt('control_exchange', default='nova',
               help='control-exchange for nova notification'),
    cfg.StrOpt('zone_id', help='Zone ID with each notification'),
    cfg.MultiStrOpt('formatv4', help='IPv4 format'),
    cfg.MultiStrOpt('format', deprecated_for_removal=True,
                    deprecated_reason="Replaced by 'formatv4/formatv6'",
                    help='format which replaced by formatv4/formatv6'),
    cfg.MultiStrOpt('formatv6', help='IPv6 format'),
]


def register_opts(conf):
    conf.register_group(SINK_GROUP)
    conf.register_opts(SINK_OPTS, group=SINK_GROUP)
    conf.register_group(SINK_FAKE_GROUP)
    conf.register_opts(SINK_FAKE_OPTS, group=SINK_FAKE_GROUP)
    conf.register_group(SINK_NEUTRON_GROUP)
    conf.register_opts(SINK_NEUTRON_OPTS, group=SINK_NEUTRON_GROUP)
    conf.register_group(SINK_NOVA_GROUP)
    conf.register_opts(SINK_NOVA_OPTS, group=SINK_NOVA_GROUP)


def list_opts():
    return {
        SINK_GROUP: SINK_OPTS,
        SINK_NEUTRON_GROUP: SINK_NEUTRON_OPTS,
        SINK_NOVA_GROUP: SINK_NOVA_OPTS,
    }
