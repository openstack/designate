# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from tempest.api_schema.dns import records as schema
from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class RecordsClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(RecordsClientJSON, self).__init__(auth_provider)
        self.service = CONF.dns.catalog_type

    def list_records(self, domain_id):
        """List all records."""
        resp, body = self.get("v1/domains/%s/records" % (domain_id))
        body = json.loads(body)
        self.validate_response(schema.list_records, resp, body)
        return resp, body['records']

    def get_record(self, domain_id, record_id):
        """Get the details of a record."""
        resp, body = self.get("v1/domains/%s/records/%s" % (domain_id,
                                                            record_id))
        body = json.loads(body)
        self.validate_response(schema.get_record, resp, body)
        return resp, body

    def delete_record(self, domain_id, record_id):
        """Delete the given record."""
        resp, body = self.delete("v1/domains/%s/records/%s" % (domain_id,
                                                               record_id))
        self.validate_response(schema.delete_record, resp, body)
        return resp, body

    def create_record(self, domain_id, name, type, data, **kwargs):
        """Createa a record."""
        post_body = {
            "name": name,
            "type": type,
            "data": data
        }
        for option in ['ttl', 'priority', 'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value
        uri = "v1/domains/%s/records" % (domain_id)
        resp, body = self.post(uri, json.dumps(post_body))
        body = json.loads(body)
        self.validate_response(schema.create_record, resp, body)
        return resp, body

    def update_record(self, domain_id, record_id, **kwargs):
        """Updates a record."""
        post_body = {}
        for option in ['name', 'type', 'data', 'ttl', 'priority',
                       'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value
        resp, body = self.put('v1/domains/%s/records/%s' % (domain_id,
                              record_id), json.dumps(post_body))
        body = json.loads(body)
        self.validate_response(schema.update_record, resp, body)
        return resp, body
