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

NETWORK_API_NEUTRON_GROUP = cfg.OptGroup(
    name='network_api:neutron', title="Configuration network api"
)

NETWORK_API_NEUTRON_OPTS = [
    cfg.ListOpt('endpoints',
                help='URL to use if None in the ServiceCatalog that is '
                     'passed by the request context. Format: <region>|<url>'),
    cfg.StrOpt('endpoint_type', default='publicURL',
               help="Endpoint type to use"),
    cfg.IntOpt('timeout',
               default=30,
               help='timeout value for connecting to neutron in seconds'),
    cfg.BoolOpt('insecure',
                default=False,
                help='if set, ignore any SSL validation issues'),
    cfg.StrOpt('ca_certificates_file',
               help='Location of ca certificates file to use for '
                    'neutron client requests.'),
    cfg.StrOpt('client_certificate_file',
               help='Location of client certificate file to use for '
                    'neutron client requests.'),
]


def register_opts(conf):
    conf.register_group(NETWORK_API_NEUTRON_GROUP)
    conf.register_opts(NETWORK_API_NEUTRON_OPTS,
                       group=NETWORK_API_NEUTRON_GROUP)


def list_opts():
    return {
        NETWORK_API_NEUTRON_GROUP: NETWORK_API_NEUTRON_OPTS
    }
