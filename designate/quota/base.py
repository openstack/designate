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

import six
from oslo_config import cfg

from designate import exceptions
from designate.plugin import DriverPlugin


@six.add_metaclass(abc.ABCMeta)
class Quota(DriverPlugin):
    """Base class for quota plugins"""
    __plugin_ns__ = 'designate.quota'
    __plugin_type__ = 'quota'

    def limit_check(self, context, tenant_id, **values):
        quotas = self.get_quotas(context, tenant_id)

        for resource, value in values.items():
            if resource in quotas:
                if value >= quotas[resource]:
                    raise exceptions.OverQuota()
            else:
                raise exceptions.QuotaResourceUnknown("%s is not a valid quota"
                                                      " resource", resource)

    def get_quotas(self, context, tenant_id):
        quotas = self.get_default_quotas(context)

        quotas.update(self._get_quotas(context, tenant_id))

        return quotas

    @abc.abstractmethod
    def _get_quotas(self, context, tenant_id):
        pass

    def get_default_quotas(self, context):
        return {
            'zones': cfg.CONF.quota_zones,
            'zone_recordsets': cfg.CONF.quota_zone_recordsets,
            'zone_records': cfg.CONF.quota_zone_records,
            'recordset_records': cfg.CONF.quota_recordset_records,
            'api_export_size': cfg.CONF.quota_api_export_size,
        }

    def get_quota(self, context, tenant_id, resource):
        quotas = self._get_quotas(context, tenant_id)

        if resource not in quotas:
            raise exceptions.QuotaResourceUnknown("%s is not a valid quota "
                                                  "resource", resource)

        return quotas[resource]

    def set_quota(self, context, tenant_id, resource, hard_limit):
        raise NotImplementedError()

    def reset_quotas(self, context, tenant_id):
        raise NotImplementedError()
