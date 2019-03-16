#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from keystoneauth1 import loading as ksa_loading
from oslo_config import cfg

KEYSTONE_GROUP = cfg.OptGroup(
    name='keystone',
    title='Access to Keystone API')


def register_opts(conf):
    conf.register_group(KEYSTONE_GROUP)
    ksa_loading.register_adapter_conf_options(conf, KEYSTONE_GROUP)
    ksa_loading.register_session_conf_options(conf, KEYSTONE_GROUP)
    conf.set_default('service_type', 'identity', group=KEYSTONE_GROUP)


def list_opts():
    return {
        KEYSTONE_GROUP: (ksa_loading.get_adapter_conf_options() +
                         ksa_loading.get_session_conf_options())
    }
