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

from tempest.api_schema.dns import domains as schema
from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class DomainsClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(DomainsClientJSON, self).__init__(auth_provider)
        self.service = CONF.dns.catalog_type

    def list_domains(self, params=None):
        """List all domains."""
        resp, body = self.get("v1/domains")
        body = json.loads(body)
        self.validate_response(schema.list_domains, resp, body)
        return resp, body['domains']

    def get_domain(self, domain_id):
        """Get the details of a domain."""
        resp, body = self.get("v1/domains/%s" % str(domain_id))
        body = json.loads(body)
        self.validate_response(schema.get_zone, resp, body)
        return resp, body

    def delete_domain(self, domain_id):
        """Delete the given domain."""
        resp, body = self.delete("v1/domains/%s" % str(domain_id))
        self.validate_response(schema.delete_zone, resp, body)
        return resp, body

    def create_domain(self, name, email, **kwargs):
        """Creates a domain."""
        post_body = {
            "name": name,
            "email": email
        }
        for option in ['ttl', 'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value
        resp, body = self.post('v1/domains', json.dumps(post_body))
        body = json.loads(body)
        self.validate_response(schema.create_zone, resp, body)
        return resp, body

    def update_domain(self, domain_id, **kwargs):
        """Updates a domain."""
        post_body = {}
        for option in ['email', 'name', 'ttl', 'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value
        resp, body = self.put('v1/domains/%s' % domain_id,
                              json.dumps(post_body))
        body = json.loads(body)
        self.validate_response(schema.update_zone, resp, body)
        return resp, body
