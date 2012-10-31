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
      Context-Type: application/json

      {
        "name": 'ns1.example.org',
        "ipv4": '192.0.2.1',
        "ipv6": '2001:db8::1'
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "id": "384a9b20-239c-11e2-81c1-0800200c9a66",
        "name": "ns1.example.org",
        "ipv4": "192.0.2.1",
        "ipv6": "2001:db8::1",
        "created_at": "2011-01-21T11:33:21Z",
        "updated_at": null
      }

   :form name: Server hostname
   :form ipv4: Server IPv4 address
   :form ipv6: Server IPv6 address
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 409: Conflict


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
          "name": "ns1.example.org",
          "ipv4": "192.0.2.1",
          "ipv6": "2001:db8::1",
          "created_at": "2011-01-21T11:33:21Z",
          "updated_at": null
        },
        {
          "id": "cf661142-e577-40b5-b3eb-75795cdc0cd7",
          "name": "ns2.example.org",
          "ipv4": "192.0.2.2",
          "ipv6": "2001:db8::2",
          "created_at": '2011-01-21T11:33:21Z",
          "updated_at": '2011-01-21T11:33:21Z"
        }
      ]

   :statuscode 200: Success
   :statuscode 401: Access Denied

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
        "name": "ns1.example.org",
        "ipv4": "192.0.2.1",
        "ipv6": "2001:db8::1",
        "created_at": "2011-01-21T11:33:21Z",
        "updated_at": null
      }

   :param server_id: The server's unique id
   :type server_id: uuid
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 404: Not Found
