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
import six
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import storage
from designate import objects
from designate.quota import base
from designate.storage import transaction


LOG = logging.getLogger(__name__)


class StorageQuota(base.Quota):
    __plugin_name__ = 'storage'

    def __init__(self):
        super(StorageQuota, self).__init__()

        # TODO(kiall): Should this be tied to central's config?
        storage_driver = cfg.CONF['service:central'].storage_driver
        self.storage = storage.get_storage(storage_driver)

    def _get_quotas(self, context, tenant_id):
        quotas = self.storage.find_quotas(context, {
            'tenant_id': tenant_id,
        })

        return dict((q['resource'], q['hard_limit']) for q in quotas)

    def get_quota(self, context, tenant_id, resource):
        context = context.deepcopy()
        context.all_tenants = True

        quota = self.storage.find_quota(context, {
            'tenant_id': tenant_id,
            'resource': resource,
        })

        return {resource: quota['hard_limit']}

    @transaction
    def set_quota(self, context, tenant_id, resource, hard_limit):
        context = context.deepcopy()
        context.all_tenants = True

        def create_quota():
            quota = objects.Quota(
                tenant_id=tenant_id, resource=resource, hard_limit=hard_limit)

            self.storage.create_quota(context, quota)

        def update_quota(quota):
            quota.hard_limit = hard_limit

            self.storage.update_quota(context, quota)

        if resource not in list(six.iterkeys(
               self.get_default_quotas(context))):
            raise exceptions.QuotaResourceUnknown("%s is not a valid quota "
                                                  "resource", resource)

        try:
            create_quota()
        except exceptions.Duplicate:
            quota = self.storage.find_quota(context, {
                'tenant_id': tenant_id,
                'resource': resource,
            })
            update_quota(quota)

        return {resource: hard_limit}

    @transaction
    def reset_quotas(self, context, tenant_id):
        context = context.deepcopy()
        context.all_tenants = True

        quotas = self.storage.find_quotas(context, {
            'tenant_id': tenant_id,
        })

        for quota in quotas:
            self.storage.delete_quota(context, quota['id'])
