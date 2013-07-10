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
from designate import exceptions
from designate.openstack.common import log as logging
from designate.quota.base import Quota
from designate.storage import api as sapi

LOG = logging.getLogger(__name__)


class StorageQuota(Quota):
    __plugin_name__ = 'storage'

    def __init__(self, storage_api=None):
        super(StorageQuota, self).__init__()

        if storage_api is None:
            storage_api = sapi.StorageAPI()

        self.storage_api = storage_api

    def _get_quotas(self, context, tenant_id):
        quotas = self.storage_api.find_quotas(context, {
            'tenant_id': tenant_id,
        })

        return dict((q['resource'], q['hard_limit']) for q in quotas)

    def get_quota(self, context, tenant_id, resource):
        quota = self.storage_api.find_quota(context, {
            'tenant_id': tenant_id,
            'resource': resource,
        })

        return {resource: quota['hard_limit']}

    def set_quota(self, context, tenant_id, resource, hard_limit):
        def create_quota():
            values = {
                'tenant_id': tenant_id,
                'resource': resource,
                'hard_limit': hard_limit,
            }

            with self.storage_api.create_quota(context, values):
                pass  # NOTE(kiall): No other systems need updating.

        def update_quota():
            values = {'hard_limit': hard_limit}

            with self.storage_api.update_quota(context, quota['id'], values):
                pass  # NOTE(kiall): No other systems need updating.

        if resource not in self.get_default_quotas(context).keys():
            raise exceptions.QuotaResourceUnknown("%s is not a valid quota "
                                                  "resource", resource)

        try:
            quota = self.storage_api.find_quota(context, {
                'tenant_id': tenant_id,
                'resource': resource,
            })
        except exceptions.NotFound:
            create_quota()
        else:
            update_quota()

        return {resource: hard_limit}

    def reset_quotas(self, context, tenant_id):
        quotas = self.storage_api.find_quotas(context, {
            'tenant_id': tenant_id,
        })

        for quota in quotas:
            with self.storage_api.delete_quota(context, quota['id']):
                pass  # NOTE(kiall): No other systems need updating.
