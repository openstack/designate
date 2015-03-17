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

from functionaltests.api.v2.models.zone_model import ZoneModel
from functionaltests.api.v2.models.zone_model import ZoneListModel


class ZoneClient(object):

    def __init__(self, client):
        self.client = client

    @classmethod
    def zones_uri(cls):
        return "/v2/zones"

    @classmethod
    def zone_uri(cls, id):
        return "{0}/{1}".format(cls.zones_uri(), id)

    @classmethod
    def deserialize(cls, resp, body, model_type):
        return resp, model_type.from_json(body)

    def list_zones(self, **kwargs):
        resp, body = self.client.get(self.zones_uri(), **kwargs)
        return self.deserialize(resp, body, ZoneListModel)

    def get_zone(self, id, **kwargs):
        resp, body = self.client.get(self.zone_uri(id))
        return self.deserialize(resp, body, ZoneModel)

    def post_zone(self, zone_model, **kwargs):
        resp, body = self.client.post(self.zones_uri(),
            body=zone_model.to_json(), **kwargs)
        return self.deserialize(resp, body, ZoneModel)

    def patch_zone(self, id, zone_model, **kwargs):
        resp, body = self.client.patch(self.zone_uri(id),
            body=zone_model.to_json(), **kwargs)
        return self.deserialize(resp, body, ZoneModel)

    def delete_zone(self, id, **kwargs):
        resp, body = self.client.delete(self.zone_uri(id), **kwargs)
        return self.deserialize(resp, body, ZoneModel)
