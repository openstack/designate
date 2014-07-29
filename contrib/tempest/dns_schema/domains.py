# Copyright 2014 Hewlett-Packard Development Company, L.P
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

list_domains = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "domains": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "created_at": {"type": "string"},
                        "description": {
                            "anyOf": [{'type': 'string'}, {"type": "null"}]},
                        "email": {"type": "string"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "serial": {"type": "number"},
                        "ttl": {"type": "number"},
                        "updated_at": {
                            "anyOf": [{'type': 'string'}, {"type": "null"}]}
                    },
                    'required': ['id', 'name', 'email', 'ttl']
                }
            }
        },
        'required': ['domains']
    }
}

create_domain = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "domain": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "description": {
                        "anyOf": [{'type': 'string'}, {"type": "null"}]},
                    "email": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "serial": {"type": "number"},
                    "ttl": {"type": "number"},
                    "updated_at": {"type": "null"}
                },
                "required": ['id', 'name', 'email', 'ttl']
            }
        }
    },
    "required": ['domain']
}

update_domain = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "domain": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "description": {
                        "anyOf": [{'type': 'string'}, {"type": "null"}]},
                    "email": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "serial": {"type": "number"},
                    "ttl": {"type": "number"},
                    "updated_at": {
                        "anyOf": [{'type': 'string'}, {"type": "null"}]}
                },
                "required": ['id', 'name', 'email', 'ttl']
            }
        }
    },
    "required": ['domain']
}

get_domain = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "domain": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "description": {
                        "anyOf": [{'type': 'string'}, {"type": "null"}]},
                    "email": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "serial": {"type": "number"},
                    "ttl": {"type": "number"},
                    "updated_at": {
                        "anyOf": [{'type': 'string'}, {"type": "null"}]}
                },
                "required": ['id', 'name', 'email', 'ttl']
            }
        }
    },
    "required": ['domain']
}

delete_domain = {
    'status_code': [200],
}
