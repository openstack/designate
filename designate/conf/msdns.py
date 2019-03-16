# Copyright 2016 Cloudbase Solutions Srl
# All Rights Reserved.
#
#    Author: Alin Balutoiu <abalutoiu@cloudbasesolutions.com>
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
from oslo_config import cfg

MSDNS_GROUP = cfg.OptGroup(
    name='backend:agent:msdns',
    title="Configuration for Microsoft DNS Server"
)
MSDNS_OPTS = [
]


def register_opts(conf):
    conf.register_group(MSDNS_GROUP)
    conf.register_opts(MSDNS_OPTS, group=MSDNS_GROUP)


def list_opts():
    return {
        MSDNS_GROUP: MSDNS_OPTS,
    }
