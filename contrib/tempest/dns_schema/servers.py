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


list_servers = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "servers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "created_at": {"type": "string"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "updated_at": {
                            "anyOf": [{'type': 'string'}, {"type": "null"}]}
                    },
                    'required': ['id', 'name']
                }
            }
        },
        'required': ['servers']
    }
}

create_server = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "server": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "updated_at": {"type": "null"}
                },
                "required": ['id', 'name']
            }
        }
    },
    "required": ['server']
}

update_server = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "server": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "updated_at": {"type": "string"}
                },
                "required": ['id', 'name']
            }
        }
    },
    "required": ['server']
}

get_server = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "server": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "updated_at": {
                        "anyOf": [{'type': 'string'}, {"type": "null"}]}
                },
                "required": ['id', 'name']
            }
        }
    },
    "required": ['server']
}

delete_server = {
    'status_code': [200],
}
