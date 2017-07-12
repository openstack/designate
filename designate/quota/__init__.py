# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from oslo_config import cfg
from oslo_log import log as logging

from designate.quota import base


LOG = logging.getLogger(__name__)

quota_opts = [
    cfg.StrOpt('quota-driver', default='storage', help='Quota driver to use'),

    cfg.IntOpt('quota-zones', default=10,
               help='Number of zones allowed per tenant'),
    cfg.IntOpt('quota-zone-recordsets', default=500,
               help='Number of recordsets allowed per zone'),
    cfg.IntOpt('quota-zone-records', default=500,
               help='Number of records allowed per zone'),
    cfg.IntOpt('quota-recordset-records', default=20,
               help='Number of records allowed per recordset'),
    cfg.IntOpt('quota-api-export-size', default=1000,
               help='Number of recordsets allowed in a zone export'),
]

cfg.CONF.register_opts(quota_opts)


def get_quota():
    quota_driver = cfg.CONF.quota_driver

    LOG.debug("Loading quota driver: %s" % quota_driver)

    cls = base.Quota.get_driver(quota_driver)

    return cls()
