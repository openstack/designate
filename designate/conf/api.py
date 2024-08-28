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
from oslo_config import cfg

API_GROUP = cfg.OptGroup(
    name='service:api',
    title="Configuration for API Service"
)

API_OPTS = [
    cfg.IntOpt('workers',
               help='Number of api worker processes to spawn'),
    cfg.IntOpt('threads', default=1000,
               help='Number of api greenthreads to spawn'),
    cfg.BoolOpt('enable_host_header', default=True,
                help='Enable host request headers'),
    cfg.StrOpt('api_base_uri', default='http://127.0.0.1:9001/',
               help='the url used as the base for all API responses,'
                    'This should consist of the scheme (http/https),'
                    'the hostname, port, and any paths that are added'
                    'to the base of Designate is URLs,'
                    'For example http://dns.openstack.example.com/dns'),
    cfg.ListOpt('listen',
                default=['0.0.0.0:9001'],
                help='API host:port pairs to listen on'),
    cfg.StrOpt('api_paste_config', default='api-paste.ini',
               help='File name for the paste.deploy config for designate-api'),
    cfg.StrOpt('auth_strategy', default='keystone',
               help='The strategy to use for auth. Supports noauth or '
                    'keystone'),
    cfg.BoolOpt('enable_api_v2', default=True,
                help='Enable the Designate V2 API'),
    cfg.BoolOpt('enable_api_admin', default=False,
                help='enable-api-admin'),
    cfg.BoolOpt('pecan_debug', default=False,
                help='Pecan HTML Debug Interface'),
]

APT_V2_OPTS = [
    cfg.ListOpt('enabled_extensions_v2', default=[],
                help='Enabled API Extensions for the V2 API'),
    cfg.IntOpt('default_limit_v2', default=20,
               help='Default per-page limit for the V2 API, a value of None '
                    'means show all results by default'),
    cfg.IntOpt('max_limit_v2', default=1000,
               help='Max per-page limit for the V2 API'),
    cfg.BoolOpt('quotas_verify_project_id', default=False,
                help='Verify that the requested Project ID for quota target '
                     'is a valid project in Keystone.'),
    cfg.BoolOpt('allow_empty_secrets_for_tsig', default=True,
                help='Allow tsig creation with empty secrets. While in theory '
                     'an empty string is valid for tsig secrets, it is highly '
                     'not recommended'),
]

API_ADMIN_OPTS = [
    cfg.ListOpt('enabled_extensions_admin', default=[],
                help='Enabled Admin API Extensions'),
    cfg.IntOpt('default_limit_admin', default=20,
               help='Default per-page limit for the Admin API, a value of None'
                    ' means show all results by default'),
    cfg.IntOpt('max_limit_admin', default=1000,
               help='Max per-page limit for the Admin API'),
]

API_MIDDLEWARE_OPTS = [
    cfg.BoolOpt('maintenance_mode', default=False,
                help='Enable API Maintenance Mode'),
    cfg.StrOpt('maintenance_mode_role', default='admin',
               help='Role allowed to bypass maintaince mode'),
]


def register_opts(conf):
    conf.register_group(API_GROUP)
    conf.register_opts(API_OPTS, group=API_GROUP)
    conf.register_opts(APT_V2_OPTS, group=API_GROUP)
    conf.register_opts(API_ADMIN_OPTS, group=API_GROUP)
    conf.register_opts(API_MIDDLEWARE_OPTS, group=API_GROUP)


def list_opts():
    return {
        API_GROUP: (API_OPTS +
                    APT_V2_OPTS +
                    API_ADMIN_OPTS +
                    API_MIDDLEWARE_OPTS)
    }
