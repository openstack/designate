# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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

DYNECT_GROUP = cfg.OptGroup(
    name='backend:dynect',
    title='Backend options for DynECT'
)

DYNECT_OPTS = [
    cfg.IntOpt('job_timeout', default=30,
               help="Timeout in seconds for pulling a job in DynECT."),
    cfg.IntOpt('timeout', help="Timeout in seconds for API Requests.",
               default=10),
    cfg.BoolOpt('timings', help="Measure requests timings.",
                default=False),
]


def register_opts(conf):
    conf.register_group(DYNECT_GROUP)
    conf.register_opts(DYNECT_OPTS, group=DYNECT_GROUP)


def list_opts():
    return {
        DYNECT_GROUP: DYNECT_OPTS,
    }
