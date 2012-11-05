Records
=======

Resource record entries are used to generate records within a zone

TODO: More detail.


Create Record
-------------

.. http:post:: /domains/(uuid:domain_id)/records

   Create a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "www.example.com",
        "type": "A",
        "data": "15.185.172.152"
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 399
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/2e32e609-3a4f-45ba-bdef-e50eacd345ad
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "2e32e609-3a4f-45ba-bdef-e50eacd345ad",
        "name": "www.example.com",
        "type": "A",
        "created_at": "2012-11-02T19:56:26.366792",
        "ttl": 3600,
        "data": "15.185.172.152",
        "domain": "/v1/domains/89acac79-38e7-497d-807c-a011e1310438",
        "self": "/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/2e32e609-3a4f-45ba-bdef-e50eacd345ad",
        "schema": "/v1/schemas/record"
      }


   :form id: record id
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: value of record
   :form domain: domain URL
   :form self: URL to domain record
   :form schema: link to the JSON schema that describes this resource 
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 409: Duplicate Domain

Update a record
---------------

.. http:put:: /domains/(uuid:domain_id)/records/(uuid:record_id)

   Updates a record

   **Example request**:

   .. sourcecode:: http

      PUT /domains/89acac79-38e7-497d-807c-a011e1310438/records/2e32e609-3a4f-45ba-bdef-e50eacd345ad
      Host: example.com
      Accept: application/json
      Content-Type: application/json
      {
        "name": "www.example.com",
        "type": "A",
        "data": "15.185.172.153"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 446
      Date: Sun, 04 Nov 2012 13:22:36 GMT

      {
        "id": "2e32e609-3a4f-45ba-bdef-e50eacd345ad",
        "name": "www.example.com",
        "type": "A",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": "2012-11-04T13:22:36.859786",
        "ttl": 3600,
        "data": "15.185.172.153",
        "domain": "/v1/domains/89acac79-38e7-497d-807c-a011e1310438",
        "self": "/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/2e32e609-3a4f-45ba-bdef-e50eacd345ad",
        "schema": "/v1/schemas/record"
      }

   :param id: record ID
   :type id: uuid
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: value of record
   :form domain: domain URL
   :form self: link to JSON schema that describes the record's domain
   :form schema: link to the JSON schema that describes this resource 
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 409: Duplicate Domain

Delete a record of a domain
---------------------------

.. http:delete:: /domains/(uuid:domain_id)/records/(uuid:record_id)

   Delete a DNS resource record

   **Example request**:

   .. sourcecode:: http

      DELETE /domains/89acac79-38e7-497d-807c-a011e1310438/records/4ad19089-3e62-40f8-9482-17cc8ccb92cb HTTP/1.1

   **Example response**:

      Content-Type: text/html; charset=utf-8
      Content-Length: 0
      Date: Sun, 04 Nov 2012 14:35:57 GMT


List a Records of a Domain
--------------------------

.. http:get:: /domains/(uuid:domain_id)/records

   Lists records of a domain

   **Example request**:

   .. sourcecode:: http

      GET /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      Content-Type: application/json
      Content-Length: 1209
      Date: Sun, 04 Nov 2012 13:58:21 GMT

      {
        "records": [
          {
            "id": "2e32e609-3a4f-45ba-bdef-e50eacd345ad"
            "name": "www.example.com",
            "type": "A",
            "ttl": 3600,
            "created_at": "2012-11-02T19:56:26.000000",
            "updated_at": "2012-11-04T13:22:36.000000",
            "data": "15.185.172.153",
            "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
            "tenant_id": null,
            "priority": null,
            "version": 1,
          },
          {
            "id": "8e9ecf3e-fb92-4a3a-a8ae-7596f167bea3"
            "name": "host1.example.com",
            "type": "A",
            "ttl": 3600,
            "created_at": "2012-11-04T13:57:50.000000",
            "updated_at": null,
            "data": "15.185.172.154",
            "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
            "tenant_id": null,
            "priority": null,
            "version": 1,
          },
          {
            "id": "4ad19089-3e62-40f8-9482-17cc8ccb92cb"
            "name": "web.example.com",
            "type": "CNAME",
            "ttl": 3600,
            "created_at": "2012-11-04T13:58:16.393735",
            "updated_at": null,
            "data": "www.example.com",
            "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
            "tenant_id": null,
            "priority": null,
            "version": 1,
          }
        ]
      }

   :param id: record ID
   :type id: uuid
   :form name: domain name
   :form type: record type
   :form ttl: time-to-live numeric value in seconds
   :form created_at: timestamp
   :form updated_at: timestamp
   :form data: value of record
   :param id: Domain ID
   :type id: uuid
   :form tenant_id: uuid of tenant
   :form priority: priority
   :form version: record version
   :statuscode 200: Success
   :statuscode 401: Access Denied
