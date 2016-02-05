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
    name='identity', title="Configuration for Keystone identity"
))

cfg.CONF.register_group(cfg.OptGroup(
    name='auth', title="Configuration for Keystone auth"
))

cfg.CONF.register_group(cfg.OptGroup(
    name='noauth', title="Configuration to run tests without Keystone"
))

cfg.CONF.register_group(cfg.OptGroup(
    name='testconfig', title="Configuration to customize how the tests run"
))

cfg.CONF.register_opts([
    cfg.StrOpt('designate_override_url',
               help="Use this instead of the endpoint in the service catalog"),

    cfg.StrOpt('uri', help="The Keystone v2 endpoint"),
    cfg.StrOpt('uri_v3', help="The Keystone v3 endpoint"),
    cfg.StrOpt('auth_version', default='v2'),
    cfg.StrOpt('region'),

    cfg.StrOpt('username'),
    cfg.StrOpt('tenant_name'),
    cfg.StrOpt('password', secret=True),
    cfg.StrOpt('domain_name'),

    cfg.StrOpt('alt_username'),
    cfg.StrOpt('alt_tenant_name'),
    cfg.StrOpt('alt_password', secret=True),
    cfg.StrOpt('alt_domain_name'),


], group='identity')

cfg.CONF.register_opts([
    cfg.StrOpt('admin_username'),
    cfg.StrOpt('admin_tenant_name'),
    cfg.StrOpt('admin_password', secret=True),
    cfg.StrOpt('admin_domain_name'),
], group="auth")

cfg.CONF.register_opts([
    cfg.StrOpt('designate_endpoint', help="The Designate API endpoint"),
    cfg.StrOpt('tenant_id', default='noauth-project'),
    cfg.StrOpt('alt_tenant_id', default='alt-project'),
    cfg.StrOpt('admin_tenant_id', default='admin-project'),
    cfg.BoolOpt('use_noauth', default=False),
], group='noauth')

cfg.CONF.register_opts([
    cfg.ListOpt('nameservers', default=["127.0.0.1:53"]),
    cfg.StrOpt('interface', default='public'),
    cfg.StrOpt('service', default='dns')
], group="designate")


cfg.CONF.register_opts([
    cfg.ListOpt('hooks', default=[],
                help="The list of request hook class names to enable"),
    cfg.StrOpt('v2_path_pattern', default='/v2/{path}',
               help="Specifies how to build the path for the request"),
    cfg.BoolOpt('no_admin_setup', default=False,
                help="Skip admin actions (like increasing quotas) in setUp()"),
    cfg.BoolOpt('disable_ssl_certificate_validation', default=False),
], group='testconfig')


def find_config_file():
    return os.environ.get(
        'TEMPEST_CONFIG', '/opt/stack/tempest/etc/tempest.conf')


def read_config():
    cfg.CONF(args=[], default_config_files=[find_config_file()])
