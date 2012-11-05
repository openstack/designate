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
      Context-Type: application/json

      {
        "name": "domain1.com",
        "ttl": 3600,
        "email": "nsadmin@example.org"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "created_at": "2012-11-01T20:09:48.094457",
        "name": "domain1.com",
        "self": "/v1/domains/89acac79-38e7-497d-807c-a011e1310438",
        "id": "89acac79-38e7-497d-807c-a011e1310438",
        "records": "/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records",
        "ttl": 3600,
        "serial": 1351800588,
        "email": "nsadmin@example.org",
        "schema": "/v1/schemas/domain"
      }


   :form created_at: timestamp
   :form name: domain name
   :form self: URL to domain
   :param id: Domain ID
   :type id: uuid
   :form records: URL to domain resource records
   :form ttl: time-to-live numeric value in seconds
   :form serial: numeric seconds
   :form email: email address
   :form schema: link to the JSON schema that describes this resource 
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

      GET /domains/09494b72b65b42979efb187f65a0553e HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "created_at": "2012-11-01T20:11:08.000000",
        "name": "domain1.com",
        "self": "/v1/domains/09494b72-b65b-4297-9efb-187f65a0553e",
        "id": "09494b72-b65b-4297-9efb-187f65a0553e",
        "records": "/v1/domains/09494b72-b65b-4297-9efb-187f65a0553e/records",
        "ttl": 3600,
        "serial": 1351800668,
        "email": "nsadmin@example.org",
        "schema": "/v1/schemas/domain"
      }

   :form created_at: timestamp
   :form name: domain name
   :form self: URL to domain
   :param id: Domain ID
   :type id: uuid
   :form records: URL to domain resource records
   :form ttl: time-to-live numeric value in seconds
   :form serial: numeric seconds
   :form email: email address
   :form schema: link to the JSON schema that describes this resource 
   :statuscode 200: Success
   :statuscode 401: Access Denied

Update a Domain
-------------

.. http:put:: /domains/(uuid:id)

   updates a domain

   **Example request**:

   .. sourcecode:: http

      PUT /domains/09494b72b65b42979efb187f65a0553e HTTP/1.1
      Host: example.com
      Accept: application/json

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
        "name": "domain1.com",
        "created_at": "2012-11-02T00:58:42.000000",
        "updated_at": "2012-11-02T01:06:07.000000",
        "id": "09494b72-b65b-4297-9efb-187f65a0553e",
        "records": "/v1/domains/09494b72-b65b-4297-9efb-187f65a0553e/records",
        "email": "nsadmin@example.org",
        "ttl": 7200,
        "serial": 1351818367,
        "self": "/v1/domains/09494b72-b65b-4297-9efb-187f65a0553e",
        "schema": "/v1/schemas/domain"
      }

   :form name: domain name
   :form created_at: timestamp
   :form updated_at: timestamp
   :param id: Domain ID
   :type id: uuid
   :form records: URL to domain resource records
   :form email: email address
   :form ttl: time-to-live numeric value in seconds
   :form serial: numeric seconds
   :form self: URL to domain
   :form schema: link to the JSON schema that describes this resource 
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

      DELETE /domains/09494b72b65b42979efb187f65a0553e HTTP/1.1
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
            "name": "domain1.com",
            "created_at": "2012-11-01T20:11:08.000000",
            "email": "nsadmin@example.org",
            "ttl": 3600,
            "serial": 1351800668,
            "id": "09494b72-b65b-4297-9efb-187f65a0553e"
          },
          {
            "name": "domain2.com",
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

