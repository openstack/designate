# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from moniker.openstack.common import cfg

cfg.CONF.register_group(cfg.OptGroup(
    name='service:central', title="Configuration for Central Service"
))

cfg.CONF.register_opts([
    cfg.StrOpt('backend-driver', default='rpc',
               help='The backend driver to use'),
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use'),
    cfg.ListOpt('enabled-notification-handlers', default=[],
                help='Enabled Notification Handlers'),
    cfg.ListOpt('reserved-domain-suffixes', default=['arpa.'],
                help='Reserved DNS domain name suffixes'),
], group='service:central')
