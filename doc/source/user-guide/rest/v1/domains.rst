Domains
=======

Domain entries are used to generate zones containing RR

TODO: More detail.


Create Domain
-------------

.. http:post:: /domains

   Create a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "domain1.com.",
        "ttl": 3600,
        "email": "nsadmin@example.org"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "id": "89acac79-38e7-497d-807c-a011e1310438",
        "name": "domain1.com.",
        "ttl": 3600,
        "serial": 1351800588,
        "email": "nsadmin@example.org",
        "created_at": "2012-11-01T20:09:48.094457",
        "updated_at": null,
        "description": null
      }


   :form created_at: timestamp
   :form updated_at: timestamp
   :form name: domain name
   :form id: uuid
   :form ttl: time-to-live numeric value in seconds
   :form serial: numeric seconds
   :form email: email address
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 409: Duplicate Domain

Get a Domain
-------------

.. http:get:: /domains/(uuid:id)

   Lists a particular domain

   **Example request**:

   .. sourcecode:: http

      GET /domains/09494b72-b65b-4297-9efb-187f65a0553e HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "id": "09494b72-b65b-4297-9efb-187f65a0553e",
        "name": "domain1.com.",
        "ttl": 3600,
        "serial": 1351800668,
        "email": "nsadmin@example.org",
        "created_at": "2012-11-01T20:11:08.000000",
        "updated_at": null,
        "description": null
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form name: domain name
   :form id: uuid
   :form ttl: time-to-live numeric value in seconds
   :form serial: numeric seconds
   :form email: email address
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied

Update a Domain
---------------

.. http:put:: /domains/(uuid:id)

   updates a domain

   **Example request**:

   .. sourcecode:: http

      PUT /domains/09494b72-b65b-4297-9efb-187f65a0553e HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "domainnamex.com",
        "ttl": 7200,
        "email": "nsadmin@example.org"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json
      Content-Length: 422
      Date: Fri, 02 Nov 2012 01:06:19 GMT

      {
        "id": "09494b72-b65b-4297-9efb-187f65a0553e",
        "name": "domain1.com.",
        "email": "nsadmin@example.org",
        "ttl": 7200,
        "serial": 1351818367,
        "created_at": "2012-11-02T00:58:42.000000",
        "updated_at": "2012-11-02T01:06:07.000000",
        "description": null
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form name: domain name
   :form id: uuid
   :form ttl: time-to-live numeric value in seconds
   :form serial: numeric seconds
   :form email: email address
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 400: Domain not found
   :statuscode 409: Duplicate Domain

Delete a Domain
---------------

.. http:delete:: /domains/(uuid:id)

   delete a domain

   **Example request**:

   .. sourcecode:: http

      DELETE /domains/09494b72-b65b-4297-9efb-187f65a0553e HTTP/1.1
      Host: example.com

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: text/html; charset=utf-8
      Content-Length: 0
      Date: Fri, 02 Nov 2012 01:26:06 GMT

   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Domain not found

Get Servers Hosting a Domain
----------------------------

.. http:get:: /domains/(uuid:id)/servers

   Lists the nameservers hosting a particular domain

   **Example request**:

   .. sourcecode:: http

      GET /domains/09494b72-b65b-4297-9efb-187f65a0553e/servers HTTP/1.1
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
          "name": "ns1.provider.com.",
          "created_at": "2011-01-21T11:33:21Z",
          "updated_at": null
        },
        {
          "id": "cf661142-e577-40b5-b3eb-75795cdc0cd7",
          "name": "ns2.provider.com.",
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
   :statuscode 404: Domain Not Found

List Domains
------------

.. http:get:: /domains

   Lists all domains

   **Example request**:

   .. sourcecode:: http

      GET /domains HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "domains": [
          {
            "name": "domain1.com.",
            "created_at": "2012-11-01T20:11:08.000000",
            "email": "nsadmin@example.org",
            "ttl": 3600,
            "serial": 1351800668,
            "id": "09494b72-b65b-4297-9efb-187f65a0553e"
          },
          {
            "name": "domain2.com.",
            "created_at": "2012-11-01T20:09:48.000000",
            "email": "nsadmin@example.org",
            "ttl": 3600,
            "serial": 1351800588,
            "id": "89acac79-38e7-497d-807c-a011e1310438"
          }
        ]
      }

   :form name: domain name
   :form created_at: timestamp
   :form email: email address
   :form ttl: time-to-live numeric value in seconds
   :form serial: numeric seconds
   :param id: Domain ID
   :type id: uuid
   :statuscode 200: Success
   :statuscode 401: Access Denied

