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

from tempest.api_schema.dns import servers as schema
from tempest.common import rest_client
from tempest import config

CONF = config.CONF


class ServersClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(ServersClientJSON, self).__init__(auth_provider)
        self.service = CONF.dns.catalog_type

    def list_servers(self, params=None):
        """List all servers."""
        resp, body = self.get("v1/servers")
        body = json.loads(body)
        self.validate_response(schema.list_servers, resp, body)
        return resp, body['servers']

    def get_server(self, server_id):
        """Get the details of a server."""
        resp, body = self.get("v1/servers/%s" % str(server_id))
        body = json.loads(body)
        self.validate_response(schema.get_server, resp, body)
        return resp, body

    def delete_server(self, server_id):
        """Delete the given server."""
        resp, body = self.delete("v1/servers/%s" % str(server_id))
        self.validate_response(schema.delete_server, resp, body)
        return resp, body

    def create_server(self, name, **kwargs):
        """Creates a server."""
        post_body = {
            "name": name,
        }
        for option in ['max-width', 'variable', 'prefix']:
            value = kwargs.get(option)
            post_param = option
            if value is not None:
                post_body[post_param] = value
        resp, body = self.post('v1/servers', json.dumps(post_body))
        body = json.loads(body)
        self.validate_response(schema.create_server, resp, body)
        return resp, body

    def update_server(self, server_id, **kwargs):
        """Updates a server."""
        name = kwargs.get('name')
        post_body = {
            'name': name
        }
        resp, body = self.put('v1/servers/%s' % server_id,
                              json.dumps(post_body))
        body = json.loads(body)
        self.validate_response(schema.update_server, resp, body)
        return resp, body
