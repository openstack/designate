..
    Copyright (C) 2014 Rackspace

    Author: Joe McBride <jmcbride@rackspace.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Record Sets and Records
=======================

A record set groups together a list of related records. It is the essential content of your zone file and is used to define the various domain to server routes for your application. Record sets are also referred to as "Resource Record Sets" or "RRSet".

The following illustrates a record set in the BIND file format:

.. sourcecode:: none
    example.org.    86400   MX  10 mail1.example.org.
                                20 mail2.example.org.
                                30 mail3.example.org.

Create Record Set (A, AAAA, CNAME, NS, and TXT)
-----------------------------------------------

The following format can be used for common record set types including A, AAAA, CNAME, NS and TXT. Simply replace the type and records with the respective values. NS record sets can only be created and deleted. Examples for MX, SSHFP, SPF and SRV will follow.

.. http:post:: /zones/(uuid:id)/recordsets

    Creates a new record set.

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
          "name" : "example.org.",
          "description" : "This is an example record set.",
          "type" : "A",
          "ttl" : 3600,
          "records" : [
              "10.1.0.2"
          ]
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "description": "This is an example record set.",
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648"
            },
            "updated_at": null,
            "records": [
                "10.1.0.2"
            ],
            "ttl": 3600,
            "id": "f7b10e9b-0cae-4a91-b162-562bc6096648",
            "name": "example.org.",
            "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
            "created_at": "2014-10-24T19:59:44.000000",
            "version": 1,
            "type": "A"
        }


    :form description: UTF-8 text field
    :form name: domain name
    :form ttl: time-to-live numeric value in seconds
    :form type: type of record set
    :form records: a list of record values

    :statuscode 201: Created
    :statuscode 401: Access Denied

Get Record Set
--------------

.. http:get:: /zones/(uuid:id)/recordsets/(uuid:id)

    Retrieves a record set with the specified record set ID.

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
            "description": "This is an example recordset.",
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648"
            },
            "updated_at": null,
            "records": [
                "10.1.0.2"
            ],
            "ttl": 3600,
            "id": "f7b10e9b-0cae-4a91-b162-562bc6096648",
            "name": "example.org.",
            "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
            "created_at": "2014-10-24T19:59:44.000000",
            "version": 1,
            "type": "A"
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

List Record Sets
----------------

.. http:get:: /zones/(uuid:id)/recordsets

    Lists all record sets for a given zone id.

    **Example Request:**

    .. sourcecode:: http

        GET /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
            "recordsets": [
                {
                    "description": null,
                    "links": {
                        "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/65ee6b49-bb4c-4e52-9799-31330c94161f"
                    },
                    "updated_at": null,
                    "records": [
                        "ns2.rackspace.com."
                    ],
                    "ttl": null,
                    "id": "65ee6b49-bb4c-4e52-9799-31330c94161f",
                    "name": "example.org.",
                    "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
                    "created_at": "2014-10-24T19:59:11.000000",
                    "version": 1,
                    "type": "NS"
                },
                {
                    "description": null,
                    "links": {
                        "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/14500cf9-bdff-48f6-b06b-5fc7491ffd9e"
                    },
                    "updated_at": "2014-10-24T19:59:46.000000",
                    "records": [
                        "ns2.rackspace.com. joe.example.org. 1414180785 3600 600 86400 3600"
                    ],
                    "ttl": null,
                    "id": "14500cf9-bdff-48f6-b06b-5fc7491ffd9e",
                    "name": "example.org.",
                    "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
                    "created_at": "2014-10-24T19:59:12.000000",
                    "version": 1,
                    "type": "SOA"
                },
                {
                    "description": "This is an example recordset.",
                    "links": {
                        "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648"
                    },
                    "updated_at": null,
                    "records": [
                        "10.1.0.2"
                    ],
                    "ttl": 3600,
                    "id": "f7b10e9b-0cae-4a91-b162-562bc6096648",
                    "name": "example.org.",
                    "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
                    "created_at": "2014-10-24T19:59:44.000000",
                    "version": 1,
                    "type": "A"
                }
            ],
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets"
            }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

Update Record Set
-----------------

.. http:put:: /zones/(uuid:id)/recordsets/(uuid:id)

    Replaces the record set with the specified details.

    In the example below, we update the TTL to 3600.

    **Request:**

    .. sourcecode:: http

        PUT /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

         {
            "description" : "I updated this example.",
            "ttl" : 60,
            "records" : [
               "10.1.0.2"
            ]
         }

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "description": "I updated this example.",
            "ttl": 60,
            "records": [
                "10.1.0.2"
            ],
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648"
            },
            "updated_at": "2014-10-24T20:15:27.000000",
            "id": "f7b10e9b-0cae-4a91-b162-562bc6096648",
            "name": "example.org.",
            "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
            "created_at": "2014-10-24T19:59:44.000000",
            "version": 2,
            "type": "A"
        }

    :form description: UTF-8 text field
    :form name: domain name
    :form ttl: time-to-live numeric value in seconds
    :form type: type of record set (can not be changed on update)
    :form records: a list of data records

    :statuscode 200: Success
    :statuscode 401: Access Denied

Delete Record Set
-----------------

.. http:delete:: zones/(uuid:id)/recordsets/(uuid:id)

    Deletes a record set with the specified record set ID.

    **Example Request:**

    .. sourcecode:: http

        DELETE /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 204 No Content

    :statuscode 204: No content

Create MX Record Set
--------------------

.. http:post:: /zones/(uuid:id)/recordsets

    Creates a new MX record set.  MX record set data format is "<priority> <host>" (e.g. "10 10.1.0.1").

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "name" : "mail.example.org.",
            "description" : "An MX recordset.",
            "type" : "MX",
            "ttl" : 3600,
            "records" : [
                "10 mail1.example.org.",
                "20 mail2.example.org.",
                "30 mail3.example.org.",
                "40 mail4.example.org."
            ]
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "description": "An MX recordset.",
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096649"
            },
            "updated_at": null,
            "records" : [
                "10 mail1.example.org.",
                "20 mail2.example.org.",
                "30 mail3.example.org.",
                "40 mail4.example.org."
            ],
            "ttl": 3600,
            "id": "f7b10e9b-0cae-4a91-b162-562bc6096649",
            "name": "mail.example.org.",
            "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
            "created_at": "2014-10-25T19:59:44.000000",
            "version": 1,
            "type": "MX"
        }


    :form description: UTF-8 text field
    :form name: domain name
    :form ttl: time-to-live numeric value in seconds
    :form type: type of record set
    :form records: a list of record values

    :statuscode 201: Created
    :statuscode 401: Access Denied

Create SSHFP Record Set
-----------------------

.. http:post:: /zones/(uuid:id)/recordsets

    Creates a new SSHFP record set. SSHFP record set data format is "<algorithm> <fingerprint-type> <fingerprint-hex>" (e.g. "1 2 aa2df857dc65c5359f02ca75ec5c4308c0100594d931e8d243a42f586257b5e8").

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
          "name" : "foo.example.org.",
          "description" : "An SSHFP recordset.",
          "type" : "SSHFP",
          "ttl" : 3600,
          "records" : [
            "1 2 aa2df857dc65c5359f02ca75ec5c4308c0100594d931e8d243a42f586257b5e8"
            ]
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "description": "An SSHFP recordset.",
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096650"
            },
            "updated_at": null,
            "records" : [
                "1 2 aa2df857dc65c5359f02ca75ec5c4308c0100594d931e8d243a42f586257b5e8"
            ],
            "ttl": 3600,
            "id": "f7b10e9b-0cae-4a91-b162-562bc6096650",
            "name": "foo.example.org.",
            "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
            "created_at": "2014-11-10T19:59:44.000000",
            "version": 1,
            "type": "SSHFP"
        }


    :form description: UTF-8 text field
    :form name: domain name
    :form ttl: time-to-live numeric value in seconds
    :form type: type of record set
    :form records: a list of record values

    :statuscode 201: Created
    :statuscode 401: Access Denied

Create SPF Record Set
---------------------

.. http:post:: /zones/(uuid:id)/recordsets

    Creates a new SPF record set. SPF record set data formatting follows standard spf record syntax.

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
          "name" : "foospf.example.org.",
          "description" : "An SPF recordset.",
          "type" : "SPF",
          "ttl" : 3600,
          "records" : [
              "v=spf1 +all"
            ]
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "description": "An SPF recordset.",
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096651"
            },
            "updated_at": null,
            "records" : [
                "v=spf1 +all"
            ],
            "ttl": 3600,
            "id": "f7b10e9b-0cae-4a91-b162-562bc6096651",
            "name": "foospf.example.org.",
            "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
            "created_at": "2014-11-10T19:59:44.000000",
            "version": 1,
            "type": "SPF"
        }


    :form description: UTF-8 text field
    :form name: domain name
    :form ttl: time-to-live numeric value in seconds
    :form type: type of record set
    :form records: a list of record values

    :statuscode 201: Created
    :statuscode 401: Access Denied

Create SRV Record Set
---------------------

.. http:post:: /zones/(uuid:id)/recordsets

    Creates a new SRV record set. SRV record set data format is "<priority> <weight> <port> <target-hostname>" (e.g. "10 0 5060 server1.example.org."). The "name" attribute should contain the service name, protocol and domain name (e.g. "_sip.tcp.example.org.").

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
          "name" : "_sip.tcp.example.org.",
          "description" : "An SRV recordset.",
          "type" : "SRV",
          "ttl" : 3600,
          "records" : [
              "10 0 5060 server1.example.org."
            ]
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "description": "An SRV recordset.",
            "links": {
                "self": "https://127.0.0.1:9001/v2/zones/2150b1bf-dee2-4221-9d85-11f7886fb15f/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096652"
            },
            "updated_at": null,
            "records" : [
                "10 0 5060 server1.example.org."
            ],
            "ttl": 3600,
            "id": "f7b10e9b-0cae-4a91-b162-562bc6096652",
            "name": "_sip.tcp.example.org.",
            "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
            "created_at": "2014-11-10T19:59:44.000000",
            "version": 1,
            "type": "SRV"
        }


    :form description: UTF-8 text field
    :form name: domain name
    :form ttl: time-to-live numeric value in seconds
    :form type: type of record set
    :form records: a list of record values

    :statuscode 201: Created
    :statuscode 401: Access Denied
