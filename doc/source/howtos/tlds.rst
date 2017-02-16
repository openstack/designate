..
    Copyright 2016 Rackspace Inc.

    Author: Tim Simmons <tim.simmons@rackspace.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Managing Top Level Domain Names
===============================

Designate allows management of the Top-Level Domains (TLDs) that users are
allowed to create zones within.

For example, it's simple to only allow users to create zones that end in
``.com.``.

By default, all TLDs are allowed in Designate, this is ok for most scenarios.

If for example you wanted to restrict to only ``.com.`` though, you could make
the following API call.

.. code-block:: http

  POST /v2/tlds/ HTTP/1.1
  Accept: application/json
  Content-Type: application/json

  {
    "name" : "com"
  }

Response:

.. code-block:: http

  HTTP/1.1 201 CREATED
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-bfcd0723-624c-4ec2-bbd5-99e985efe8db

  {
   "name": "com",
   "links": {
     "self": "http://127.0.0.1:9001/v2/tlds/cfee7486-7ce4-4851-9c38-7b0fe3d42ee9"
   },
   "created_at": "2016-05-18 05:07:58",
   "updated_at": null,
   "id": "cfee7486-7ce4-4851-9c38-7b0fe3d42ee9",
   "description": "tld description"
  }


Now, if someone were to try and create ``example.net.``, they would encounter
an error:

.. code-block:: http

  HTTP/1.1 400 BAD REQUEST
  Content-Type: application/json
  X-Openstack-Request-Id: req-f841013b-c6cd-4f0b-a9ea-bdb65db7a334"

  {
    "message": "Invalid TLD",
    "code": 400,
    "type": "invalid_zone_name",
    "request_id": "req-f841013b-c6cd-4f0b-a9ea-bdb65db7a334"
  }

TLDs can be deleted, just like an other resource in the API,
``DELETE /v2/tlds/<id>``.
