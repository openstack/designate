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

from functionaltests.api.v2.models.quotas_model import QuotasModel


class QuotasClient(object):

    def __init__(self, client):
        self.client = client

    @classmethod
    def quotas_uri(cls, tenant_id):
        return "/admin/quotas/" + tenant_id

    @classmethod
    def deserialize(cls, resp, body, model_type):
        return resp, model_type.from_json(body)

    def get_quotas(self, tenant_id, **kwargs):
        resp, body = self.client.get(self.quotas_uri(tenant_id), **kwargs)
        return self.deserialize(resp, body, QuotasModel)

    def patch_quotas(self, tenant_id, quotas_model, **kwargs):
        resp, body = self.client.patch(self.quotas_uri(tenant_id),
            body=quotas_model.to_json(), **kwargs)
        return self.deserialize(resp, body, QuotasModel)

    def delete_quotas(self, tenant_id, **kwargs):
        resp, body = self.client.patch(self.quotas_uri(tenant_id), **kwargs)
        return self.deserialize(resp, body, QuotasModel)
