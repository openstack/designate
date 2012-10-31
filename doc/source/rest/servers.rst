Servers
=======

Contents:

.. toctree::
   :maxdepth: 2


.. http:get:: /servers/(uuid:server_id)

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
          "id": '',
          "name": '',
          "ipv4": '',
          "ipv6": '',
          "created_at": null,
          "updated_at": null
        },
        {
          "id": '',
          "name": '',
          "ipv4": '',
          "ipv6": '',
          "created_at": null,
          "updated_at": null
        }
      ]

   :statuscode 200: Success
   :statuscode 401: Access Denied
