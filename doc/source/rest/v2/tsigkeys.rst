..
    Copyright 2015 NEC Corporation.  All rights reserved.

    Author: Sonu Kumar <sonu.kumar@nectechnologies.in>

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
Tsigkey
=======

Transaction signatures (TSIG) is a mechanism used to secure DNS messages and
to provide secure server-to-server communication (usually between master and
slave server, but can be extended for dynamic updates as well).

Transaction Signatures, or TSIG for short, add cryptographic signatures as a
method of authenticating a DNS conversation. It uses a shared secret to
establish trust between the communicating parties.


Create Tsigkeys
===============

.. http:post:: /tsigkeys

  Create a new Tsigkey.

  **Example request**:

  .. code-block:: http

     POST /tsigkeys HTTP/1.1
     Host: 127.0.0.1:9001
     Accept: application/json
     Content-Type: application/json

     {
        "name": "Example key",
        "algorithm": "hmac-sha256",
        "secret": "SomeSecretKey",
        "scope": "POOL",
        "resource_id": "6ca6baef-3305-4ad0-a52b-a82df5752b62"
     }

  **Example response**:

  .. code-block:: http

    HTTP/1.1 201 Created
    Location: http://127.0.0.1:9001/v2/tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2
    Content-Length: 350
    Content-Type: application/json; charset=UTF-8

    {
      "links": {
          "self": "http://127.0.0.1:9001/v2/tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
      },
      "name": "test-key",
      "algorithm": "hmac-sha256",
      "resource_id": "6ca6baef-3305-4ad0-a52b-a82df5752b62",
      "created_at": "2015-12-21T09:48:15.000000",
      "updated_at": null,
      "secret": "SomeSecretKey",
      "scope": "POOL",
      "id": "5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
    }

    :form name: TSIG Key Name.
    :form algorithm: TSIG Algorithm.
    :form resource_id: Pool id or Zone id
    :form secret: TSIG Secret.
    :form scope: TSIG Scope.

    :statuscode 201: Created
    :statuscode 202: Accepted
    :statuscode 401: Access Denied


Get Tsigkeys
============

.. http:get:: /tsigkeys

  Get the list of Tsigkeys.

  **Example request**:

  .. code-block:: http

    GET /tsigkeys HTTP/1.1
    Host: 127.0.0.1:9001
    Accept: application/json

  **Example response**:

  .. code-block:: http

     HTTP/1.1 200 OK
     Content-Length: 776
     Content-Type: application/json; charset=UTF-8

     {
       "tsigkeys": [
          {
            "links": {
               "self": "http://127.0.0.1:9001/v2/tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
            },
          "name": "test-key",
          "algorithm": "hmac-sha256",
          "resource_id": "6ca6baef-3305-4ad0-a52b-a82df5752b62",
          "created_at": "2015-12-21T09:48:15.000000",
          "updated_at": null,
          "secret": "SomeSecretKey",
          "scope": "POOL",
          "id": "5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
          },
          {
           "links": {
              "self": "http://127.0.0.1:9001/v2/tsigkeys/319c58fd-a0e0-4d69-a854-98bc49594419"
           },
           "name": "test-key-2",
           "algorithm": "hmac-sha256",
           "resource_id": "6ca6baef-3305-4ad0-a52b-a82df5752b62",
           "created_at": "2015-12-21T09:51:06.000000",
           "updated_at": null,
           "secret": "SomeSecretKey",
           "scope": "POOL",
           "id": "319c58fd-a0e0-4d69-a854-98bc49594419"}
       ],
       "links": {
          "self": "http://127.0.0.1:9001/v2/tsigkeys"}
     }

    :statuscode 200: Success
    :statuscode 401: Access Denied



Get Tsigkey
===========

.. http:get:: /tsigkeys/(uuid:id)

    Retrieves a tsigkey with the specified tsigkey's ID.

    **Example request:**

    .. sourcecode:: http

        GET /v2/tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2 HTTP/1.1
        Host: 127.0.0.1:9001
        Content-Type: application/json
        Accept: application/json

    **Example response:**

    .. sourcecode:: http

       Content-Length: 350
       Content-Type: application/json; charset=UTF-8
       X-Openstack-Request-Id: req-d8cd7f24-a735-400b-9a4b-79e175efc923
       Date: Mon, 21 Dec 2015 09:59:26 GMT

       {
          "links": {
             "self": "http://127.0.0.1:9001/v2/tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
          },
          "name": "test-key",
          "algorithm": "hmac-sha256",
          "resource_id": "6ca6baef-3305-4ad0-a52b-a82df5752b62",
          "created_at": "2015-12-21T09:48:15.000000",
          "updated_at": null,
          "secret": "SomeSecretKey",
          "scope": "POOL",
          "id": "5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
      }



Update Tsigkey
==============

.. http:patch:: /tsigkeys/(uuid:id)

   Update a Tsigkey with the specified tsigkey's id.

   **Example request**:

   .. code-block:: http

     PATCH /tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2 HTTP/1.1
     Host: 127.0.0.1:9001
     Accept: application/json
     Content-Type: application/json

     {
       "name": "example_tsigkey",
       "scope": "ZONE"
     }

   **Example response**:

   .. code-block:: http

      HTTP/1.1 200 OK
      Content-Length: 381
      Content-Type: application/json; charset=UTF-8

      {
         "links": {
            "self": "http://127.0.0.1:9001/v2/tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
         },
         "name": "example_tsigkey",
         "algorithm": "hmac-sha256",
         "resource_id": "6ca6baef-3305-4ad0-a52b-a82df5752b62",
         "created_at": "2015-12-21T09:48:15.000000",
         "updated_at": "2015-12-21T10:02:18.000000",
         "secret": "SomeSecretKey",
         "scope": "ZONE",
         "id": "5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2"
      }

    :form name: TSIG Key Name.
    :form algorithm: TSIG Algorithm.
    :form resource_id: Pool id or Zone id
    :form secret: TSIG Secret.
    :form scope: TSIG Scope.

    :statuscode 200: Success
    :statuscode 202: Accepted
    :statuscode 401: Access Denied

Remove Tsigkey
==============

.. http:delete:: /tsigkeys/(uuid:id)

   Remove a Tsigkey with the specified tsigkey's id.

   **Example request**:

   .. code-block:: http

     DELETE /tsigkeys/5fa28ce8-68e3-4fdf-89c1-ed9f151b83d2 HTTP/1.1
     Accept: application/json

   **Example response**:

   .. code-block:: http

     HTTP/1.1 204 No Content
     Content-Length: 0

   :statuscode 400: Bad Request
   :statuscode 204: Successfully Deleted
