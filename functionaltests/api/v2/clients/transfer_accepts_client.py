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

from functionaltests.api.v2.models.transfer_accepts_model import \
    TransferAcceptsModel
from functionaltests.api.v2.models.transfer_accepts_model import \
    TransferAcceptsListModel
from functionaltests.common.client import ClientMixin


class TransferAcceptClient(ClientMixin):

    def transfer_accepts_uri(self, filters=None):
        return self.create_uri("/zones/tasks/transfer_accepts",
                               filters=filters)

    def transfer_accept_uri(self, transfer_request_id):
        return "{0}/{1}".format(self.transfer_accepts_uri(),
                                transfer_request_id)

    def list_transfer_accepts(self, zone_id, filters=None, **kwargs):
        resp, body = self.client.get(
            self.transfer_accepts_uri(filters), **kwargs)
        return self.deserialize(resp, body, TransferAcceptsListModel)

    def get_transfer_accept(self, zone_id, transfer_request_id, **kwargs):
        resp, body = self.client.get(self.transfer_accept_uri(
            transfer_request_id),
            **kwargs)
        return self.deserialize(resp, body, TransferAcceptsModel)

    def post_transfer_accept(self, transfer_request_model, **kwargs):
        resp, body = self.client.post(
            self.transfer_accepts_uri(),
            body=transfer_request_model.to_json(),
            **kwargs)
        return self.deserialize(resp, body, TransferAcceptsModel)

    def put_transfer_accept(self, zone_id, transfer_request_id,
                            transfer_request_model, **kwargs):
        resp, body = self.client.put(self.transfer_accept_uri(
            transfer_request_id),
            body=transfer_request_model.to_json(), **kwargs)
        return self.deserialize(resp, body, TransferAcceptsModel)

    def delete_transfer_accept(self, zone_id, transfer_request_id, **kwargs):
        resp, body = self.client.delete(
            self.transfer_accept_uri(zone_id, transfer_request_id), **kwargs)
        return self.deserialize(resp, body, TransferAcceptsModel)
