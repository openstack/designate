"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os

from oslo_config import cfg

cfg.CONF.register_group(cfg.OptGroup(
    name='identity', title="Configuration for Keystone auth"
))

cfg.CONF.register_group(cfg.OptGroup(
    name='noauth', title="Configuration to run tests without Keystone"
))

cfg.CONF.register_opts([
    cfg.StrOpt('designate_override_url',
               help="Use this instead of the endpoint in the service catalog"),

    cfg.StrOpt('uri', help="The Keystone v2 endpoint"),
    cfg.StrOpt('uri_v3', help="The Keystone v3 endpoint"),
    cfg.StrOpt('auth_version', default='v2'),
    cfg.StrOpt('region', default='RegionOne'),

    cfg.StrOpt('username'),
    cfg.StrOpt('tenant_name'),
    cfg.StrOpt('password', secret=True),
    cfg.StrOpt('domain_name'),

    cfg.StrOpt('alt_username'),
    cfg.StrOpt('alt_tenant_name'),
    cfg.StrOpt('alt_password', secret=True),
    cfg.StrOpt('alt_domain_name'),

    cfg.StrOpt('admin_username'),
    cfg.StrOpt('admin_tenant_name'),
    cfg.StrOpt('admin_password', secret=True),
    cfg.StrOpt('admin_domain_name'),
], group='identity')

cfg.CONF.register_opts([
    cfg.StrOpt('designate_endpoint', help="The Designate API endpoint"),
    cfg.StrOpt('tenant_id', default='noauth-project'),
    cfg.StrOpt('alt_tenant_id', default='alt-project'),
    cfg.StrOpt('admin_tenant_id', default='admin-project'),
    cfg.BoolOpt('use_noauth', default=False),
], group='noauth')


cfg.CONF.register_opts([
    cfg.ListOpt('nameservers', default=["127.0.0.1:53"])
], group="designate")


def find_config_file():
    return os.environ.get(
        'TEMPEST_CONFIG', '/opt/stack/tempest/etc/tempest.conf')


def read_config():
    cfg.CONF(args=[], default_config_files=[find_config_file()])
