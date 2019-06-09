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

# Set some proxy options (Used for clients that need to communicate via a
# proxy)
PROXY_GROUP = cfg.OptGroup(
    name='proxy',
    title="Configuration for Client Proxy"
)

PROXY_OPTS = [
    cfg.StrOpt('http_proxy',
               help='Proxy HTTP requests via this proxy.'),
    cfg.StrOpt('https_proxy',
               help='Proxy HTTPS requests via this proxy'),
    cfg.ListOpt('no_proxy', default=[],
                help='These addresses should not be proxied'),
]


def register_opts(conf):
    conf.register_group(PROXY_GROUP)
    conf.register_opts(PROXY_OPTS, group=PROXY_GROUP)


def list_opts():
    return {
        PROXY_GROUP: PROXY_OPTS
    }
