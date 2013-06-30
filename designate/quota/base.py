# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import abc
from oslo.config import cfg
from designate import exceptions
from designate.plugin import Plugin


class Quota(Plugin):
    """ Base class for quota plugins """
    __metaclass__ = abc.ABCMeta
    __plugin_ns__ = 'designate.quota'
    __plugin_type__ = 'quota'

    def get_tenant_quotas(self, context, tenant_id):
        """
        Get quotas for a tenant.

        :param context: RPC Context.
        :param tenant_id: Tenant ID to fetch quotas for
        """
        quotas = {
            'domains': cfg.CONF.quota_domains,
            'domain_records': cfg.CONF.quota_domain_records,
        }

        quotas.update(self._get_tenant_quotas(context, tenant_id))

        return quotas

    def limit_check(self, context, tenant_id, **values):
        quotas = self.get_tenant_quotas(context, tenant_id)

        for resource, value in values.items():
            if resource in quotas:
                if value >= quotas[resource]:
                    raise exceptions.OverQuota()
            else:
                raise exceptions.QuotaResourceUnknown()

    @abc.abstractmethod
    def _get_tenant_quotas(self, context, tenant_id):
        pass
