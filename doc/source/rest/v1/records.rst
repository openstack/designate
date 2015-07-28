Records
=======

Resource record entries are used to generate records within a zone

TODO: More detail.

.. note:: V1 API has been deprecated since the Kilo release.

.. note:: The "description" field on Records cannot be accessed from the V2
    API. Likewise, the "description" field on Record Sets cannot be accessed
    from the V1 API.



Create Record
-------------

.. http:post:: /domains/(uuid:domain_id)/records

   Create an A record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "www.example.com.",
        "type": "A",
        "data": "192.0.2.3"
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
        "name": "www.example.com.",
        "type": "A",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "ttl": null,
        "priority": null,
        "data": "192.0.2.3",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: IPv4 address
   :form domain_id: domain ID
   :form priority: must be null for 'A' record
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create a AAAA record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "www.example.com.",
        "type": "AAAA",
        "data": "2001:db8:0:1234:0:5678:9:12"
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 303
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666677778888
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666677778888",
        "name": "www.example.com.",
        "type": "AAAA",
        "created_at": "2013-01-07T00:00:00.000000",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "priority": null,
        "ttl": null,
        "data": "2001:db8:0:1234:0:5678:9:12",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: IPv6 address
   :form domain_id: domain ID
   :form priority: must be null for 'AAAA' records
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record


   Create an MX record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "example.com.",
        "type": "MX",
        "data": "mail.example.com.",
        "priority": 10
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 420
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666677778888
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666677778888",
        "name": "www.example.com.",
        "type": "MX",
        "created_at": "2013-01-07T00:00:00.000000",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "priority": 10,
        "ttl": null,
        "data": "mail.example.com.",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: value of record
   :form domain_id: domain ID
   :form priority: priority of MX record
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create a CNAME record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "www.example.com.",
        "type": "CNAME",
        "data": "example.com."
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 303
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666677778889
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666677778889",
        "name": "www.example.com.",
        "type": "CNAME",
        "created_at": "2013-01-07T00:00:00.000000",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "priority": null,
        "ttl": null,
        "data": "example.com.",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: alias for the CNAME
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: CNAME
   :form domain_id: domain ID
   :form priority: must be null for 'CNAME' records
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create a TXT record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "www.example.com.",
        "type": "TXT",
        "data": "This is a TXT record"
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 303
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666677778899
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666677778899",
        "name": "www.example.com.",
        "type": "TXT",
        "created_at": "2013-01-07T00:00:00.000000",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "priority": null,
        "ttl": null,
        "data": "This is a TXT record",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: Text associated with record.
   :form domain_id: domain ID
   :form priority: must be null for 'TXT' records
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create an SRV record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "_sip._tcp.example.com.",
        "type": "SRV",
        "data": "0 5060 sip.example.com.",
        "priority": 30
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 399
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666677778999
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-66667777899",
        "name": "_sip._tcp.example.com.",
        "type": "SRV",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "ttl": null,
        "priority" : 30,
        "data": "0 5060 sip.example.com.",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: name of service
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: weight port target
   :form domain_id: domain ID
   :form priority: priority of SRV record
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create an NS record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": ".example.com.",
        "type": "NS",
        "data": "ns1.example.com."
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 399
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666677789999
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666677789999",
        "name": ".example.com.",
        "type": "NS",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "ttl": null,
        "priority" : null,
        "data": "ns1.example.com",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: record name
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamps
   :form ttl: time-to-live numeric value in seconds
   :form data: record value
   :form domain_id: domain ID
   :form priority: must be null for 'NS' record
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create a PTR record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: 2.3.192.in-addr.arpa.
      Accept: application/json
      Content-Type: application/json

      {
        "name": "1.2.3.192.in-addr.arpa.",
        "type": "PTR",
        "data": "www.example.com."
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 399
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666677889999
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666677889999",
        "name": "1.2.3.192.in-addr.arpa.",
        "type": "PTR",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "ttl": null,
        "priority" : null,
        "data": "www.example.com",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: PTR record name
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: DNS record value
   :form domain_id: domain ID
   :form priority: must be null for 'PTR' record
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create an SPF record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": ".example.com.",
        "type": "SPF",
        "data": "v=spf1 +mx a:colo.example.com/28 -all"
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 399
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666678889999
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666678889999",
        "name": ".example.com.",
        "type": "SPF",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "ttl": null,
        "priority" : null,
        "data": "v=spf1 +mx a:colo.example.com/28 -all",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: name of record
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: record value
   :form domain_id: domain ID
   :form priority: must be null for 'SPF' record
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record

   Create an SSHFP record for a domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/89acac79-38e7-497d-807c-a011e1310438/records HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "name": "www.example.com.",
        "type": "SSHFP",
        "data": "2 1 6c3c958af43d953f91f40e0d84157f4fe7b4a898"
      }


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 399
      Location: http://localhost:9001/v1/domains/89acac79-38e7-497d-807c-a011e1310438/records/11112222-3333-4444-5555-666778889999
      Date: Fri, 02 Nov 2012 19:56:26 GMT

      {
        "id": "11112222-3333-4444-5555-666778889999",
        "name": "www.example.com.",
        "type": "SSHFP",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": null,
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "ttl": null,
        "priority" : null,
        "data": "2 1 6c3c958af43d953f91f40e0d84157f4fe7b4a898",
        "description": null
      }


   :param domain_id: domain ID
   :form id: record ID
   :form name: name of record
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form ttl: time-to-live numeric value in seconds
   :form data: algorithm number, fingerprint type, fingerprint
   :form domain_id: domain ID
   :form priority: must be null for 'SSHFP' record
   :form description: UTF-8 text field
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: Not Found
   :statuscode 409: Duplicate Record


Get a Record
-------------

.. http:get:: /domains/(uuid:domain_id)/records/(uuid:id)

   Get a particular record

   **Example request**:

   .. sourcecode:: http

      GET /domains/09494b72b65b42979efb187f65a0553e/records/2e32e609-3a4f-45ba-bdef-e50eacd345ad HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "id": "2e32e609-3a4f-45ba-bdef-e50eacd345ad",
        "name": "www.example.com.",
        "type": "A",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": "2012-11-04T13:22:36.859786",
        "priority": null,
        "ttl": 3600,
        "data": "15.185.172.153",
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "description": null
      }

   :param domain_id: Domain ID
   :param id: Record ID
   :form id: record ID
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form priority: priority of record
   :form ttl: time-to-live numeric value in seconds
   :form data: value of record
   :form description: UTF-8 text field
   :form domain_id: domain ID
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 404: Record Not Found

Update a record
---------------

.. http:put:: /domains/(uuid:domain_id)/records/(uuid:id)

   Updates a record

   **Example request**:

   .. sourcecode:: http

      PUT /domains/89acac79-38e7-497d-807c-a011e1310438/records/2e32e609-3a4f-45ba-bdef-e50eacd345ad
      Host: example.com
      Accept: application/json
      Content-Type: application/json
      {
        "name": "www.example.com.",
        "type": "A",
        "data": "192.0.2.5"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json
      Content-Length: 446
      Date: Sun, 04 Nov 2012 13:22:36 GMT

      {
        "id": "2e32e609-3a4f-45ba-bdef-e50eacd345ad",
        "name": "www.example.com.",
        "type": "A",
        "created_at": "2012-11-02T19:56:26.366792",
        "updated_at": "2012-11-04T13:22:36.859786",
        "priority": null,
        "ttl": 3600,
        "data": "192.0.2.5",
        "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
        "description": null
      }

   :param domain_id: domain ID
   :param id: record ID
   :form id: record ID
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form priority: priority of record
   :form ttl: time-to-live numeric value in seconds
   :form data: value of record
   :form description: UTF-8 text field
   :form domain_id: domain ID
   :statuscode 200: Success
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 409: Duplicate Record

Delete a record
---------------

.. http:delete:: /domains/(uuid:domain_id)/records/(uuid:id)

   Delete a DNS resource record

   **Example request**:

   .. sourcecode:: http

      DELETE /domains/89acac79-38e7-497d-807c-a011e1310438/records/4ad19089-3e62-40f8-9482-17cc8ccb92cb HTTP/1.1

   :param domain_id: domain ID
   :param id: record ID

   **Example response**:

      Content-Type: text/html; charset=utf-8
      Content-Length: 0
      Date: Sun, 04 Nov 2012 14:35:57 GMT


List Records in a Domain
------------------------

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
            "id": "2e32e609-3a4f-45ba-bdef-e50eacd345ad",
            "name": "www.example.com.",
            "type": "A",
            "ttl": 3600,
            "created_at": "2012-11-02T19:56:26.000000",
            "updated_at": "2012-11-04T13:22:36.000000",
            "data": "15.185.172.153",
            "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
            "tenant_id": null,
            "priority": null,
            "description": null,
            "version": 1
          },
          {
            "id": "8e9ecf3e-fb92-4a3a-a8ae-7596f167bea3",
            "name": "host1.example.com.",
            "type": "A",
            "ttl": 3600,
            "created_at": "2012-11-04T13:57:50.000000",
            "updated_at": null,
            "data": "15.185.172.154",
            "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
            "tenant_id": null,
            "priority": null,
            "description": null,
            "version": 1
          },
          {
            "id": "4ad19089-3e62-40f8-9482-17cc8ccb92cb",
            "name": "web.example.com.",
            "type": "CNAME",
            "ttl": 3600,
            "created_at": "2012-11-04T13:58:16.393735",
            "updated_at": null,
            "data": "www.example.com.",
            "domain_id": "89acac79-38e7-497d-807c-a011e1310438",
            "tenant_id": null,
            "priority": null,
            "description": null,
            "version": 1
          }
        ]
      }

   :param domain_id: domain ID
   :form id: record id
   :form name: name of record FQDN
   :form type: type of record
   :form created_at: timestamp
   :form updated_at: timestamp
   :form priority: priority of record
   :form ttl: time-to-live numeric value in seconds
   :form data: value of record
   :form description: UTF-8 text field
   :form domain_id: domain ID
   :statuscode 200: Success
   :statuscode 401: Access Denied
