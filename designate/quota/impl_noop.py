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
from oslo_log import log as logging

from designate.quota import base

LOG = logging.getLogger(__name__)


class NoopQuota(base.Quota):
    __plugin_name__ = 'noop'

    def _get_quotas(self, context, tenant_id):
        """Internal Get Quotas used by get_quotas"""
        return {}

    def get_quota(self, context, tenant_id, resource):
        """Get Quota"""

    def set_quota(self, context, tenant_id, resource, hard_limit):
        """Set Quota"""

    def reset_quotas(self, context, tenant_id):
        """Reset Quotas"""
