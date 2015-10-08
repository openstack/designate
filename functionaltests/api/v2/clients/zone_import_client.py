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
from functionaltests.api.v2.models.zone_import_model import ZoneImportModel
from functionaltests.api.v2.models.zone_import_model import ZoneImportListModel
from functionaltests.common.client import ClientMixin
from functionaltests.common import utils


class ZoneImportClient(ClientMixin):

    def zone_imports_uri(self, filters=None):
        return self.create_uri("/zones/tasks/imports", filters=filters)

    def zone_import_uri(self, id):
        return "{0}/{1}".format(self.zone_imports_uri(), id)

    def list_zone_imports(self, filters=None, **kwargs):
        resp, body = self.client.get(
            self.zone_imports_uri(filters), **kwargs)
        return self.deserialize(resp, body, ZoneImportListModel)

    def get_zone_import(self, id, **kwargs):
        resp, body = self.client.get(self.zone_import_uri(id))
        return self.deserialize(resp, body, ZoneImportModel)

    def post_zone_import(self, zonefile_data, **kwargs):
        headers = {'Content-Type': 'text/dns'}
        resp, body = self.client.post(self.zone_imports_uri(),
            body=zonefile_data, headers=headers, **kwargs)
        return self.deserialize(resp, body, ZoneImportModel)

    def delete_zone_import(self, id, **kwargs):
        resp, body = self.client.delete(self.zone_import_uri(id), **kwargs)
        return resp, body

    def wait_for_zone_import(self, zone_import_id):
        utils.wait_for_condition(
            lambda: self.is_zone_import_active(zone_import_id))

    def is_zone_import_active(self, zone_import_id):
        resp, model = self.get_zone_import(zone_import_id)
        # don't have assertEqual but still want to fail fast
        assert resp.status == 200
        if model.status == 'COMPLETE':
            return True
        elif model.status == 'ERROR':
            raise Exception("Saw ERROR status")
        return False
