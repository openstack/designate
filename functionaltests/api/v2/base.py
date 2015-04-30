"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from functionaltests.api.v2.clients.quotas_client import QuotasClient
from functionaltests.api.v2.models.quotas_model import QuotasModel
from functionaltests.common.base import BaseDesignateTest


class DesignateV2Test(BaseDesignateTest):

    def __init__(self, *args, **kwargs):
        super(DesignateV2Test, self).__init__(*args, **kwargs)

    def increase_quotas(self, user):
        QuotasClient.as_user('admin').patch_quotas(
            QuotasClient.as_user(user).tenant_id,
            QuotasModel.from_dict({
                'quota': {
                    'zones': 9999999,
                    'recordset_records': 9999999,
                    'zone_records': 9999999,
                    'zone_recordsets': 9999999}}))
