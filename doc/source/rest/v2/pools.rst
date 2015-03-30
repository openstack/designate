..
    Copyright (C) 2015 Rackspace

    Author: Eric Larson <eric.larson@rackspace.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


=======
 Pools
=======

Pools are collection of backend DNS servers such as bind9. The backend
servers in a pool are responsible for answering DNS queries.

.. note::

   Currently there is a default pool that is created. Please be aware,
   this will change in the future.


Create Pool
===========

.. http:post:: /pools

  Create a new Pool.

  **Example request**:

  .. code-block:: http

     POST /pools HTTP/1.1
     Host: example.com
     Accept: application/json
     Content-Type: application/json

     {
        "name": "Example Pool",
        "ns_records": [
            {
              "hostname": "ns1.example.org.",
              "priority": 1
            }
        ]
     }


  **Example response**:

  .. code-block:: http

    HTTP/1.1 201 Created
    Location: http://127.0.0.1:9001/v2/pools/d1716333-8c16-490f-85ee-29af36907605
    Content-Type: application/json; charset=UTF-8

    {
      "description": null,
      "id": "d1716333-8c16-490f-85ee-29af36907605",
      "project_id": "noauth-project",
      "created_at": "2015-02-23T21:56:33.000000",
      "attributes": null,
      "ns_records": [
        {
          "hostname": "ns1.example.org.",
          "priority": 1
        }
      ],
      "links": {
        "self": "http://127.0.0.1:9001/v2/pools/d1716333-8c16-490f-85ee-29af36907605"
      },
      "name": "example_pool",
      "updated_at": null
    }

  :form name: UTF-8 text field
  :form description: a description of the pool
  :form tenant_id: the UUID of the tenant
  :form provisioner: the type backend that should be used
  :form attributes: meta data for the pool
  :form ns_records: a list of ns_records as fully qualified domains

  :statuscode 201: Created
  :statuscode 400: Bad Request
  :statuscode 401: Access Denied


Get Pools
=========

.. http:get:: /pools

  Get the list of Pools. This resource supports the
  :doc:`collections` API.

  **Example request**:

  .. code-block:: http

    GET /pools HTTP/1.1
    Host: example.com
    Accept: application/json


  **Example response**:

  .. code-block:: http

    HTTP/1.1 200 OK
    Content-Length: 755
    Content-Type: application/json; charset=UTF-8

    {
      "metadata": null,
      "links": {
        "self": "http://127.0.0.1:9001/v2/pools"
      },
      "pools": [
        {
          "description": null,
          "id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
          "project_id": null,
          "created_at": "2015-02-18T22:18:58.000000",
          "attributes": null,
          "ns_records": [
            {
              "hostname": "ns1.example.org.",
              "priority": 1
            }
          ],
          "links": {
            "self": "http://127.0.0.1:9001/v2/pools/794ccc2c-d751-44fe-b57f-8894c9f5c842"
          },
          "name": "default",
          "updated_at": "2015-02-19T15:59:44.000000"
        },
        {
          "description": null,
          "id": "d1716333-8c16-490f-85ee-29af36907605",
          "project_id": "noauth-project",
          "created_at": "2015-02-23T21:56:33.000000",
          "attributes": null,
          "ns_records": [
            {
              "hostname": "ns2.example.org.",
              "priority": 1
            }
          ],
          "links": {
            "self": "http://127.0.0.1:9001/v2/pools/d1716333-8c16-490f-85ee-29af36907605"
          },
          "name": "example_pool",
          "updated_at": null
        }
      ]
    }

  :statuscode 200: OK
  :statuscode 400: Bad Request


Get Pool
========

.. http:get:: /pools/(uuid:id)

  Get a specific Pool using the Pool's uuid id.

  **Example request**:

  .. code-block:: http

    GET /pools/d1716333-8c16-490f-85ee-29af36907605 HTTP/1.1
    Host: example.com
    Accept: application/json

  **Example response**:

  .. code-block:: http

    HTTP/1.1 200 OK
    Content-Length: 349
    Content-Type: application/json; charset=UTF-8

    {
      "description": null,
      "id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
      "project_id": null,
      "created_at": "2015-02-18T22:18:58.000000",
      "attributes": null,
      "ns_records": [
        {
          "hostname": "ns1.example.org.",
          "priority": 1
        }
      ],
      "links": {
        "self": "http://127.0.0.1:9001/v2/pools/794ccc2c-d751-44fe-b57f-8894c9f5c842"
      },
      "name": "default",
      "updated_at": "2015-02-19T15:59:44.000000"
    }

  :statuscode 200: OK
  :statuscode 400: Bad Request



Update Pool
===========

.. http:patch:: /pools/(uuid:id)

  Update a Pool.

  **Example request**:

  .. code-block:: http

    PATCH /pools/794ccc2c-d751-44fe-b57f-8894c9f5c842 HTTP/1.1
    Host: example.com
    Accept: application/json
    Content-Type: application/json

    {
        "ns_records": [
            {
                "hostname": "ns1.example.org.",
                "priority": 1
            },
            {
                "hostname": "ns3.example.org.",
                "priority": 2
            }
        ],
    }

  **Example response**:

  .. code-block:: http

    HTTP/1.1 200 OK
    Content-Length: 369
    Content-Type: application/json; charset=UTF-8

    {
      "description": null,
      "id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
      "project_id": null,
      "created_at": "2015-02-18T22:18:58.000000",
      "attributes": null,
      "ns_records": [
        {
          "hostname": "ns1.example.org.",
          "priority": 1
        }
        {
          "hostname": "ns3.example.org.",
          "priority": 2
        }
      ],
      "links": {
        "self": "http://127.0.0.1:9001/v2/pools/794ccc2c-d751-44fe-b57f-8894c9f5c842"
      },
      "name": "default",
      "updated_at": "2015-02-24T17:39:07.000000"
    }

  .. note::

    When updating the Pool definition document, take care to ensure
    that any existing values are included when updating a field. For
    example, if we used

    .. code-block:: json

      {
          "ns_records": [
              {
                "hostname": "ns3.example.org.",
                "priority": 2
              }
          ]
      }

    This would **replace** the value of the `ns_records` key.

    It is a good practice to peform a GET and mutate the result
    accordingly.

  :statuscode 202: Accepted
  :statuscode 400: Bad Request
  :statuscode 409: Conflict


Remove Pool
===========

.. http:delete:: /pools/(uuid:id)

  Remove a Pool. When deleting a Pool, the Pool cannot contain any
  zones.

  **Example request**:

  .. code-block:: http

    DELETE /pools HTTP/1.1
    Accept: application/json

  **Example response**:

  .. code-block:: http

    HTTP/1.1 204 No Content
    Content-Length: 0

  :statuscode 400: Bad Request
  :statuscode 204: Successfully Deleted
