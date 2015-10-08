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

from functionaltests.api.v2.models.transfer_requests_model import \
    TransferRequestsModel
from functionaltests.api.v2.models.transfer_requests_model import \
    TransferRequestsListModel
from functionaltests.common.client import ClientMixin


class TransferRequestClient(ClientMixin):

    def create_transfer_requests_uri(self, zone_id, filters=None):
        return self.create_uri(
            "/zones/{0}/tasks/transfer_requests".format(zone_id),
            filters=filters,
        )

    def transfer_requests_uri(self, filters=None):
        return self.create_uri(
            "/zones/tasks/transfer_requests",
            filters=filters,
        )

    def transfer_request_uri(self, transfer_request_id):
        return self.create_uri(
            "/zones/tasks/transfer_requests/{0}".format(transfer_request_id)
        )

    def list_transfer_requests(self, filters=None, **kwargs):
        resp, body = self.client.get(
            self.transfer_requests_uri(filters), **kwargs)
        return self.deserialize(resp, body, TransferRequestsListModel)

    def get_transfer_request(self, transfer_request_id, **kwargs):
        resp, body = self.client.get(self.transfer_request_uri(
            transfer_request_id),
            **kwargs)
        return self.deserialize(resp, body, TransferRequestsModel)

    def post_transfer_request(self, zone_id, transfer_request_model=None,
                              **kwargs):
        resp, body = self.client.post(
            self.create_transfer_requests_uri(zone_id),
            body=transfer_request_model.to_json(),
            **kwargs)
        return self.deserialize(resp, body, TransferRequestsModel)

    def post_transfer_request_empty_body(self, zone_id, **kwargs):
        resp, body = self.client.post(
            self.create_transfer_requests_uri(zone_id),
            body=None,
            **kwargs)
        return self.deserialize(resp, body, TransferRequestsModel)

    def put_transfer_request(self, transfer_request_id,
                             transfer_request_model, **kwargs):
        resp, body = self.client.put(self.transfer_request_uri(
            transfer_request_id),
            body=transfer_request_model.to_json(), **kwargs)
        return self.deserialize(resp, body, TransferRequestsModel)

    def delete_transfer_request(self, transfer_request_id, **kwargs):
        resp, body = self.client.delete(
            self.transfer_request_uri(transfer_request_id), **kwargs)
        # the body is empty on a successful delete
        if body:
            return self.deserialize(resp, body, TransferRequestsModel)
        return resp, body
