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

from functionaltests.api.v2.models.recordset_model import RecordsetModel
from functionaltests.api.v2.models.recordset_model import RecordsetListModel
from functionaltests.common.client import ClientMixin
from functionaltests.common import utils


class RecordsetClient(ClientMixin):

    @classmethod
    def recordsets_uri(cls, zone_id):
        return "/v2/zones/{0}/recordsets".format(zone_id)

    @classmethod
    def recordset_uri(cls, zone_id, recordset_id):
        return "{0}/{1}".format(cls.recordsets_uri(zone_id), recordset_id)

    def list_recordsets(self, zone_id, **kwargs):
        resp, body = self.client.get(self.recordsets_uri(zone_id), **kwargs)
        return self.deserialize(resp, body, RecordsetListModel)

    def get_recordset(self, zone_id, recordset_id, **kwargs):
        resp, body = self.client.get(self.recordset_uri(zone_id, recordset_id),
                                     **kwargs)
        return self.deserialize(resp, body, RecordsetModel)

    def post_recordset(self, zone_id, recordset_model, **kwargs):
        resp, body = self.client.post(self.recordsets_uri(zone_id),
            body=recordset_model.to_json(), **kwargs)
        return self.deserialize(resp, body, RecordsetModel)

    def put_recordset(self, zone_id, recordset_id, recordset_model, **kwargs):
        resp, body = self.client.put(self.recordset_uri(zone_id, recordset_id),
            body=recordset_model.to_json(), **kwargs)
        return self.deserialize(resp, body, RecordsetModel)

    def delete_recordset(self, zone_id, recordset_id, **kwargs):
        resp, body = self.client.delete(
            self.recordset_uri(zone_id, recordset_id), **kwargs)
        return self.deserialize(resp, body, RecordsetModel)

    def wait_for_recordset(self, zone_id, recordset_id):
        utils.wait_for_condition(
            lambda: self.is_recordset_active(zone_id, recordset_id))

    def wait_for_404(self, zone_id, recordset_id):
        utils.wait_for_condition(
            lambda: self.is_recordset_404(zone_id, recordset_id))

    def is_recordset_active(self, zone_id, recordset_id):
        resp, model = self.get_recordset(
            zone_id, recordset_id)
        assert resp.status == 200
        if model.status == 'ACTIVE':
            return True
        elif model.status == 'ERROR':
            raise Exception("Saw ERROR status")
        return False

    def is_recordset_404(self, zone_id, recordset_id):
        try:
            self.get_recordset(zone_id, recordset_id)
        except NotFound:
            return True
        return False
