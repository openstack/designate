# Copyright 2015 Dyn Inc.
#
# Author: Yasha Bubnov <ybubnov@dyn.com>
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

DENOMINATOR_GROUP = cfg.OptGroup(
    name='backend:agent:denominator',
    title='Backend options for Denominator',
)

DENOMINATOR_OPTS = [
    cfg.StrOpt('name', default='fake',
               help='Name of the affected provider',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.StrOpt('config_file', default='/etc/denominator.conf',
               help='Path to Denominator configuration file',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
]


def register_opts(conf):
    conf.register_group(DENOMINATOR_GROUP)
    conf.register_opts(DENOMINATOR_OPTS, group=DENOMINATOR_GROUP)


def list_opts():
    return {
        DENOMINATOR_GROUP: DENOMINATOR_OPTS,
    }
