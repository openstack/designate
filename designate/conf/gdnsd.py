# Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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

GDNSD_GROUP = cfg.OptGroup(
    name='backend:agent:gdnsd',
    title="Configuration for gdnsd backend"
)
GDNSD_OPTS = [
    cfg.StrOpt('gdnsd_cmd_name',
               help='gdnsd executable path or rootwrap command name',
               default='gdnsd',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.StrOpt('confdir_path',
               help='gdnsd configuration directory path',
               default='/etc/gdnsd',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
    cfg.StrOpt('query_destination', default='127.0.0.1',
               help='Host to query when finding zones',
               deprecated_for_removal=True,
               deprecated_since='Antelope(2023.1)',
               deprecated_reason='The agent framework is deprecated.'),
]


def register_opts(conf):
    conf.register_group(GDNSD_GROUP)
    conf.register_opts(GDNSD_OPTS, group=GDNSD_GROUP)


def list_opts():
    return {
        GDNSD_GROUP: GDNSD_OPTS,
    }
