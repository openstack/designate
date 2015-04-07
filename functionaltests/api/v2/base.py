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

from tempest_lib.exceptions import NotFound

from functionaltests.api.v2.clients.recordset_client import RecordsetClient
from functionaltests.api.v2.clients.zone_client import ZoneClient
from functionaltests.api.v2.clients.quotas_client import QuotasClient
from functionaltests.api.v2.models.quotas_model import QuotasModel
from functionaltests.common.base import BaseDesignateTest


class DesignateV2Test(BaseDesignateTest):

    def __init__(self, *args, **kwargs):
        super(DesignateV2Test, self).__init__(*args, **kwargs)
        self.zone_client = ZoneClient(self.base_client)
        self.quotas_client = QuotasClient(self.base_client)
        self.recordset_client = RecordsetClient(self.base_client)

    def wait_for_zone(self, zone_id):
        self.wait_for_condition(lambda: self.is_zone_active(zone_id))

    def wait_for_zone_404(self, zone_id):
        self.wait_for_condition(lambda: self.is_zone_404(zone_id))

    def is_zone_active(self, zone_id):
        resp, model = self.zone_client.get_zone(zone_id)
        self.assertEqual(resp.status, 200)
        if model.status == 'ACTIVE':
            return True
        elif model.status == 'ERROR':
            raise Exception("Saw ERROR status")
        return False

    def is_zone_404(self, zone_id):
        try:
            # tempest_lib rest client raises exceptions on bad status codes
            resp, model = self.zone_client.get_zone(zone_id)
        except NotFound:
            return True
        return False

    def increase_quotas(self):
        self.quotas_client.patch_quotas(
            self.quotas_client.client.tenant_id,
            QuotasModel.from_dict({
                'quota': {
                    'zones': 9999999,
                    'recordset_records': 9999999,
                    'zone_records': 9999999,
                    'zone_recordsets': 9999999}}))
