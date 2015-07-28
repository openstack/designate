Servers
=======

Server entries are used to generate NS records for zones..

TODO: More detail.

TODO: Server Groups Concept.


Create Server
-------------

.. http:post:: /servers

   Create a DNS server

   **Example request**:

   .. sourcecode:: http

      POST /servers HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "ns1.example.org."
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "id": "384a9b20-239c-11e2-81c1-0800200c9a66",
        "name": "ns1.example.org.",
        "created_at": "2011-01-21T11:33:21Z",
        "updated_at": null
      }

   :form name: Server hostname
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 409: Conflict

Get Server
----------

.. http:get:: /servers/(uuid:server_id)

   Lists all configured DNS servers

   **Example request**:

   .. sourcecode:: http

      GET /servers/384a9b20-239c-11e2-81c1-0800200c9a66 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "id": "384a9b20-239c-11e2-81c1-0800200c9a66",
        "name": "ns1.example.org.",
        "created_at": "2011-01-21T11:33:21Z",
        "updated_at": null
      }

   :param server_id: The server's unique id
   :type server_id: uuid
   :form name: Server hostname
   :form created_at: timestamp
   :form updated_at: timestamp
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 404: Not Found

Update Server
-------------

.. http:put:: /servers/(uuid:server_id)

   Create a DNS server

   **Example request**:

   .. sourcecode:: http

      PUT /servers/879c1100-9c92-4244-bc83-9535ee6534d0 HTTP/1.1
      Content-Type: application/json
      Accept: application/json
      Content-Type: application/json

      {
        "name": "ns1.example.org."
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "id": "879c1100-9c92-4244-bc83-9535ee6534d0",
        "name": "ns1.example.org.",
        "created_at": "2012-11-02T02:55:44.000000",
        "updated_at": "2012-11-02T02:58:41.993556"
      }

   :form id: UUID server_id
   :form name: Server hostname
   :form created_at: timestamp
   :form updated_at: timestamp
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 404: Server Not Found
   :statuscode 409: Duplicate Server

List Servers
------------

.. http:get:: /servers

   Lists all configured DNS servers

   **Example request**:

   .. sourcecode:: http

      GET /servers HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      [
        {
          "id": "384a9b20-239c-11e2-81c1-0800200c9a66",
          "name": "ns1.example.org.",
          "created_at": "2011-01-21T11:33:21Z",
          "updated_at": null
        },
        {
          "id": "cf661142-e577-40b5-b3eb-75795cdc0cd7",
          "name": "ns2.example.org.",
          "created_at": "2011-01-21T11:33:21Z",
          "updated_at": "2011-01-21T11:33:21Z"
        }
      ]

   :form id: UUID server_id
   :form name: Server hostname
   :form created_at: timestamp
   :form updated_at: timestamp
   :statuscode 200: Success
   :statuscode 401: Access Denied

Delete Server
-------------

.. http:delete:: /servers/(uuid:server_id)

   Deletes a specified server

  **Example request**:

  .. sourcecode:: http

     DELETE /servers/5d1d7879-b778-4f77-bb95-02f4a5a224d8 HTTP/1.1
     Host: example.com

  **Example response**

  .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: text/html; charset=utf-8
      Content-Length: 0
      Date: Thu, 01 Nov 2012 10:00:00 GMT

   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 404: Not Found

