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

from functionaltests.api.v2.models.tld_model import TLDModel
from functionaltests.api.v2.models.tld_model import TLDListModel
from functionaltests.common.client import ClientMixin


class TLDClient(ClientMixin):

    @classmethod
    def tlds_uri(cls):
        return "/v2/tlds"

    @classmethod
    def tld_uri(cls, tld_id):
        return "{0}/{1}".format(cls.tlds_uri(), tld_id)

    def list_tlds(self, **kwargs):
        resp, body = self.client.get(self.tlds_uri(), **kwargs)
        return self.deserialize(resp, body, TLDListModel)

    def get_tld(self, tld_id, **kwargs):
        resp, body = self.client.get(self.tld_uri(tld_id))
        return self.deserialize(resp, body, TLDModel)

    def post_tld(self, tld_model, **kwargs):
        resp, body = self.client.post(
            self.tlds_uri(),
            body=tld_model.to_json(), **kwargs)
        return self.deserialize(resp, body, TLDModel)

    def patch_tld(self, tld_id, tld_model, **kwargs):
        resp, body = self.client.patch(
            self.tld_uri(tld_id),
            body=tld_model.to_json(), **kwargs)
        return self.deserialize(resp, body, TLDModel)

    def delete_tld(self, tld_id, **kwargs):
        return self.client.delete(self.tld_uri(tld_id), **kwargs)
