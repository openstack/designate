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
``.com.`` TLD.

By default, all TLDs are allowed in Designate, this is ok for most scenarios.

If for example you wanted to restrict to only ``.com.`` though, you could make
the following API call.

.. code-block:: http

    POST /v2/tlds HTTP/1.1
    Accept: application/json
    Content-Type: application/json

    {
      "name": "com"
    }

Response:

.. code-block:: http

    HTTP/1.1 201 CREATED
    Content-Type: application/json
    X-Openstack-Request-Id: req-432e72b4-f4e1-4f9c-8e35-53decc752260

    {
      "id": "2f8bc76d-1701-4323-a101-248e09471342",
      "name": "com",
      "description": null,
      "created_at": "2020-06-01T16:25:44.000000",
      "updated_at": null,
      "links": {
        "self": "http://127.0.0.1:9001/v2/tlds/2f8bc76d-1701-4323-a101-248e09471342"
      }
    }

Using the command line client:

.. code-block:: console

    $ openstack tld create --name com
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | created_at  | 2020-06-01T16:25:44.000000           |
    | description | None                                 |
    | id          | 2f8bc76d-1701-4323-a101-248e09471342 |
    | name        | com                                  |
    | updated_at  | None                                 |
    +-------------+--------------------------------------+

Now, if someone were to try and create ``example.net.``, they would encounter
an error:

.. code-block:: http

    POST /v2/zones HTTP/1.1
    Accept: application/json
    Content-Type: application/json

    {
      "name": "example.net.",
      "type": "PRIMARY",
      "email": "admin@example.net"
    }

.. code-block:: http

    HTTP/1.1 400 BAD REQUEST
    Content-Type: application/json
    X-Openstack-Request-Id: req-3a8985fd-0155-4dd4-a7fb-584b140f1f59

    {
      "code": 400,
      "type": "invalid_zone_name",
      "message": "Invalid TLD",
      "request_id": "req-3a8985fd-0155-4dd4-a7fb-584b140f1f59"
    }

Using the command line client:

.. code-block:: console

    $ openstack zone create --email admin@example.net example.net.
    Invalid TLD

TLDs can be deleted, just like many other resources in the API, using
``DELETE /v2/tlds/<id>``:

.. code-block:: http

    DELETE /v2/tlds/2f8bc76d-1701-4323-a101-248e09471342 HTTP/1.1
    Accept: application/json
    Content-Type: application/json

Or by using the command line client:

.. code-block:: console

    $ openstack tld delete com
    TLD com was deleted
