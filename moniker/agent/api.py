# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common.rpc.proxy import RpcProxy

DEFAULT_VERSION = '1.0'

LOG = logging.getLogger(__name__)
RPC = RpcProxy(cfg.CONF.agent_topic, DEFAULT_VERSION)


# Domain Methods
def create_domain(context, domain):
    msg = {
        'method': 'create_domain',
        'args': {
            'domain': domain,
        },
    }

    return RPC.fanout_cast(context, msg)


def update_domain(context, domain):
    msg = {
        'method': 'update_domain',
        'args': {
            'domain': domain,
        },
    }

    return RPC.fanout_cast(context, msg)


def delete_domain(context, domain_id):
    msg = {
        'method': 'delete_domain',
        'args': {
            'domain_id': domain_id,
        },
    }

    return RPC.fanout_cast(context, msg)


# Record Methods
def create_record(context, domain, record):
    msg = {
        'method': 'create_record',
        'args': {
            'domain': domain,
            'record': record,
        },
    }

    return RPC.fanout_cast(context, msg)


def update_record(context, domain, record):
    msg = {
        'method': 'update_record',
        'args': {
            'domain': domain,
            'record': record,
        },
    }

    return RPC.fanout_cast(context, msg)


def delete_record(context, domain, record_id):
    msg = {
        'method': 'delete_record',
        'args': {
            'domain': domain,
            'record_id': record_id,
        },
    }

    return RPC.fanout_cast(context, msg)
