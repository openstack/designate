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
import abc

import designate.conf
from designate import exceptions
from designate.plugin import DriverPlugin


CONF = designate.conf.CONF


class Quota(DriverPlugin, metaclass=abc.ABCMeta):
    """Base class for quota plugins"""
    __plugin_ns__ = 'designate.quota'
    __plugin_type__ = 'quota'

    def limit_check(self, context, tenant_id, **values):
        resources_exceeded = []
        quotas = self.get_quotas(context, tenant_id)

        for resource, value in values.items():
            if resource in quotas:
                # Setting the resource quota to a negative value will make
                # the resource unlimited
                if quotas[resource] >= 0 and value > quotas[resource]:
                    resources_exceeded.append(resource)
            else:
                raise exceptions.QuotaResourceUnknown(
                    f"'{resource}' is not a valid quota resource."
                )

        if resources_exceeded:
            resources_exceeded.sort(key=len)
            raise exceptions.OverQuota(
                'Quota exceeded for %s.' % ', '.join(resources_exceeded)
            )

    def get_quotas(self, context, tenant_id):
        quotas = self.get_default_quotas(context)
        quotas.update(self._get_quotas(context, tenant_id))

        return quotas

    def get_default_quotas(self, context):
        return {
            'zones': CONF.quota_zones,
            'zone_recordsets': CONF.quota_zone_recordsets,
            'zone_records': CONF.quota_zone_records,
            'recordset_records': CONF.quota_recordset_records,
            'api_export_size': CONF.quota_api_export_size,
        }

    @abc.abstractmethod
    def _get_quotas(self, context, tenant_id):
        """Internal Get Quotas used by get_quotas"""

    @abc.abstractmethod
    def get_quota(self, context, tenant_id, resource):
        """Get Quota"""

    @abc.abstractmethod
    def set_quota(self, context, tenant_id, resource, hard_limit):
        """Set Quota"""

    @abc.abstractmethod
    def reset_quotas(self, context, tenant_id):
        """Reset Quotas"""
