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

from functionaltests.api.v2.models.recordset_model import RecordsetModel
from functionaltests.api.v2.models.recordset_model import RecordsetListModel


class RecordsetClient(object):

    def __init__(self, client):
        self.client = client

    @classmethod
    def recordsets_uri(cls, zone_id):
        return "/v2/zones/{0}/recordsets".format(zone_id)

    @classmethod
    def recordset_uri(cls, zone_id, recordset_id):
        return "{0}/{1}".format(cls.recordsets_uri(zone_id), recordset_id)

    @classmethod
    def deserialize(cls, resp, body, model_type):
        return resp, model_type.from_json(body)

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
