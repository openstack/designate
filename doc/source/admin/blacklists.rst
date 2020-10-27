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

Blacklisting Domain Names
=========================

Zone and recordset names can be blacklisted in Designate, disallowing
the creation of certain names, specified by regular expressions.

The simple use case here could be "I don't want anyone to be able to
create anything with ``mycompany.com.`` in it!", or maybe disallowing
subzones on a certain zone. Or simply disallowing the creation of a single
zone, like ``google.com.``.

If wanted to blacklist ``example.com.`` and all of it's subdomains, we could
make the following API calls.

.. code-block:: http

  POST /v2/blacklists/ HTTP/1.1
  Accept: application/json
  Content-Type: application/json

  {
    "pattern" : "^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
    "description" : "This blacklists *.example.com."
  }

Response:

.. code-block:: http

  HTTP/1.1 201 CREATED
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-bfcd0723-624c-4ec2-bbd5-99e985efe8db

  {
     "description": "This blacklists *.example.com.",
     "links": {
       "self": "http://127.0.0.1:9001/v2/blacklists/af91edb5-ede8-453f-af13-feabdd088f9c"
     },
     "pattern": "^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
     "created_at": "2016-05-20 06:15:42",
     "updated_at": null,
     "id": "af91edb5-ede8-453f-af13-feabdd088f9c"
  }


Now, if someone were to try and create ``foo.example.com.``,
or ``example.com.`` they would encounter an error:

.. code-block:: http

  HTTP/1.1 400 BAD REQUEST
  Content-Type: application/json
  X-Openstack-Request-Id: req-b7be7770-ec4f-4573-b4db-70f95475f691

  {
    "message": "Blacklisted zone name",
    "code": 400,
    "type": "invalid_zone_name",
     "request_id": "req-b7be7770-ec4f-4573-b4db-70f95475f691"
  }

Blacklists can be deleted, just like an other resource in the API,
``DELETE /v2/blacklists/<id>``.

Regular Expressions
-------------------

The regular expressions used here can be a bit difficult to wrap your mind
around at first. Try using a tool like https://www.debuggex.com/

It's important to note that the regular expressions we enter are similar
to Python regular expressions, but we need to escape certain characters
when we make HTTP calls.

This means that if you wanted to debug this regex:

``^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$``

you're really working with this regex:

``^([A-Za-z0-9_\\-]+\.)*example\.com\.$``
