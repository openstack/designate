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

from functionaltests.api.v2.models.zone_model import ZoneModel
from functionaltests.api.v2.models.zone_model import ZoneListModel
from functionaltests.common.client import ClientMixin
from functionaltests.common import utils


class ZoneClient(ClientMixin):

    def zones_uri(self, filters=None):
        return self.create_uri("/zones", filters=filters)

    def zone_uri(self, id):
        return "{0}/{1}".format(self.zones_uri(), id)

    def list_zones(self, filters=None, **kwargs):
        resp, body = self.client.get(self.zones_uri(filters), **kwargs)
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

    def wait_for_zone(self, zone_id):
        utils.wait_for_condition(lambda: self.is_zone_active(zone_id))

    def wait_for_zone_404(self, zone_id):
        utils.wait_for_condition(lambda: self.is_zone_404(zone_id))

    def is_zone_active(self, zone_id):
        resp, model = self.get_zone(zone_id)
        # don't have assertEqual but still want to fail fast
        assert resp.status == 200
        if model.status == 'ACTIVE':
            return True
        elif model.status == 'ERROR':
            raise Exception("Saw ERROR status")
        return False

    def is_zone_404(self, zone_id):
        try:
            # tempest_lib rest client raises exceptions on bad status codes
            resp, model = self.get_zone(zone_id)
        except NotFound:
            return True
        return False

    def zones_dot_json(self, filters=None, **kwargs):
        uri = self.create_uri("/zones.json", filters=filters)
        resp, body = self.client.get(uri, **kwargs)
        return self.deserialize(resp, body, ZoneListModel)
