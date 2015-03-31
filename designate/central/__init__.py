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
    cfg.StrOpt('storage-driver', default='sqlalchemy',
               help='The storage driver to use'),
    cfg.ListOpt('enabled-notification-handlers', default=[],
                help='Enabled Notification Handlers'),
    cfg.IntOpt('max_domain_name_len', default=255,
               help="Maximum domain name length"),
    cfg.IntOpt('max_recordset_name_len', default=255,
               help="Maximum recordset name length",
               deprecated_name='max_record_name_len'),
    cfg.StrOpt('managed_resource_email', default='hostmaster@example.com',
               help='E-Mail for Managed resources'),
    cfg.StrOpt('managed_resource_tenant_id',
               default="00000000-0000-0000-0000-000000000000",
               help="The Tenant ID that will own any managed resources."),
    cfg.StrOpt('min_ttl', default="None", help="Minimum TTL allowed"),
    # TODO(betsy): Move to Pool Service once that is written
    cfg.StrOpt('default_pool_id',
               default='794ccc2c-d751-44fe-b57f-8894c9f5c842',
               help="The name of the default pool"),
], group='service:central')
