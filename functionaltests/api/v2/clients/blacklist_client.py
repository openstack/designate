# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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

from functionaltests.api.v2.models.blacklist_model import BlacklistModel
from functionaltests.api.v2.models.blacklist_model import BlacklistListModel
from functionaltests.common.client import ClientMixin


class BlacklistClient(ClientMixin):

    @classmethod
    def blacklists_uri(cls, filters=None):
        url = "/v2/blacklists"
        if filters:
            url = cls.add_filters(url, filters)
        return url

    @classmethod
    def blacklist_uri(cls, blacklist_id):
        return "{0}/{1}".format(cls.blacklists_uri(), blacklist_id)

    def list_blacklists(self, filters=None, **kwargs):
        resp, body = self.client.get(self.blacklists_uri(filters), **kwargs)
        return self.deserialize(resp, body, BlacklistListModel)

    def get_blacklist(self, blacklist_id, **kwargs):
        resp, body = self.client.get(self.blacklist_uri(blacklist_id))
        return self.deserialize(resp, body, BlacklistModel)

    def post_blacklist(self, blacklist_model, **kwargs):
        resp, body = self.client.post(
            self.blacklists_uri(),
            body=blacklist_model.to_json(), **kwargs)
        return self.deserialize(resp, body, BlacklistModel)

    def patch_blacklist(self, blacklist_id, blacklist_model, **kwargs):
        resp, body = self.client.patch(
            self.blacklist_uri(blacklist_id),
            body=blacklist_model.to_json(), **kwargs)
        return self.deserialize(resp, body, BlacklistModel)

    def delete_blacklist(self, blacklist_id, **kwargs):
        return self.client.delete(self.blacklist_uri(blacklist_id), **kwargs)
