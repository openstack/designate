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
from oslo.config import cfg

cfg.CONF.register_group(cfg.OptGroup(
    name='service:central', title="Configuration for Central Service"
))

cfg.CONF.register_opts([
    cfg.IntOpt('workers', default=None,
               help='Number of worker processes to spawn'),
    cfg.StrOpt('backend-driver', default='fake',
               help='The backend driver to use'),
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use'),
    cfg.ListOpt('enabled-notification-handlers', default=[],
                help='Enabled Notification Handlers'),
    cfg.ListOpt('domain-name-blacklist',
                default=['\\.arpa\\.$', '\\.novalocal\\.$', '\\.localhost\\.$',
                         '\\.localdomain\\.$', '\\.local\\.$'],
                help='DNS domain name blacklist'),
    cfg.StrOpt('accepted-tlds-file', default='tlds-alpha-by-domain.txt',
               help='Accepted TLDs'),
    cfg.StrOpt('effective-tlds-file', default='effective_tld_names.dat',
               help='Effective TLDs'),
    cfg.IntOpt('max_domain_name_len', default=255,
               help="Maximum domain name length"),
    cfg.IntOpt('max_record_name_len', default=255,
               help="Maximum record name length"),
], group='service:central')
