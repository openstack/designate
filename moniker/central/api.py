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
RPC = RpcProxy(cfg.CONF.central_topic, DEFAULT_VERSION)


def create_server(context, values):
    msg = {
        'method': 'create_server',
        'args': {
            'values': values,
        },
    }

    return RPC.call(context, msg)


def get_servers(context, criterion=None):
    msg = {
        'method': 'get_servers',
        'args': {
            'criterion': criterion,
        },
    }

    return RPC.call(context, msg)


def get_server(context, server_id):
    msg = {
        'method': 'get_server',
        'args': {
            'server_id': server_id,
        },
    }

    return RPC.call(context, msg)


def update_server(context, server_id, values):
    msg = {
        'method': 'update_server',
        'args': {
            'server_id': server_id,
            'values': values,
        },
    }

    return RPC.call(context, msg)


def delete_server(context, server_id):
    msg = {
        'method': 'delete_server',
        'args': {
            'server_id': server_id,
        },
    }

    return RPC.call(context, msg)


# Domain Methods
def create_domain(context, values):
    msg = {
        'method': 'create_domain',
        'args': {
            'values': values,
        },
    }

    return RPC.call(context, msg)


def get_domains(context, criterion=None):
    msg = {
        'method': 'get_domains',
        'args': {
            'criterion': criterion,
        },
    }

    return RPC.call(context, msg)


def get_domain(context, domain_id):
    msg = {
        'method': 'get_domain',
        'args': {
            'domain_id': domain_id,
        },
    }

    return RPC.call(context, msg)


def update_domain(context, domain_id, values):
    msg = {
        'method': 'update_domain',
        'args': {
            'domain_id': domain_id,
            'values': values,
        },
    }

    return RPC.call(context, msg)


def delete_domain(context, domain_id):
    msg = {
        'method': 'delete_domain',
        'args': {
            'domain_id': domain_id,
        },
    }

    return RPC.call(context, msg)


# Record Methods
def create_record(context, domain_id, values):
    msg = {
        'method': 'create_record',
        'args': {
            'domain_id': domain_id,
            'values': values,
        },
    }

    return RPC.call(context, msg)


def get_records(context, domain_id, criterion=None):
    msg = {
        'method': 'get_records',
        'args': {
            'domain_id': domain_id,
            'criterion': criterion,
        },
    }

    return RPC.call(context, msg)


def get_record(context, domain_id, record_id):
    msg = {
        'method': 'get_record',
        'args': {
            'domain_id': domain_id,
            'record_id': record_id,
        },
    }

    return RPC.call(context, msg)


def update_record(context, domain_id, record_id, values):
    msg = {
        'method': 'update_record',
        'args': {
            'domain_id': domain_id,
            'record_id': record_id,
            'values': values,
        },
    }

    return RPC.call(context, msg)


def delete_record(context, domain_id, record_id):
    msg = {
        'method': 'delete_record',
        'args': {
            'domain_id': domain_id,
            'record_id': record_id,
        },
    }

    return RPC.call(context, msg)


def sync_all(context):
    msg = {
        'method': 'sync_all',
        'args': {},
    }

    return RPC.call(context, msg)


def sync_domain(context, domain_id):
    msg = {
        'method': 'sync_domain',
        'args': {
            'domain_id': domain_id,
        },
    }

    return RPC.call(context, msg)


def sync_record(context, domain_id, record_id):
    msg = {
        'method': 'sync_record',
        'args': {
            'domain_id': domain_id,
            'record_id': record_id,
        },
    }

    return RPC.call(context, msg)
