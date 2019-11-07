# Copyright 2012-2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import os

from oslo_config import cfg

WSDL_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), '..', 'resources', 'wsdl', 'EnhancedDNS.xml'
    )
)

AKAMAI_GROUP = cfg.OptGroup(
    name='backend:akamai',
    title='Backend options for Akamai'
)

AKAMAI_OPTS = [
    cfg.StrOpt('enhanceddns_wsdl',
               default='file://%s' % WSDL_PATH,
               sample_default=os.path.join('/path', 'to', 'EnhancedDNS.xml'),
               help='Akamai EnhancedDNS WSDL URL'),
]


def register_opts(conf):
    conf.register_group(AKAMAI_GROUP)
    conf.register_opts(AKAMAI_OPTS, group=AKAMAI_GROUP)


def list_opts():
    return {
        AKAMAI_GROUP: AKAMAI_OPTS,
    }
