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

.. note:: The "description" field on Records cannot be accessed from the V2
    API. Likewise, the "description" field on Record Sets cannot be accessed
    from the V1 API.

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
    :statuscode 202: Accepted
    :statuscode 401: Access Denied

Get Record Set
--------------

Two APIs can be used to retrieve a single recordset. One with zone ID in url, the other without.

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

.. http:get:: /recordsets/(uuid:id)

    If http client follows redirect, API returns a 200. Otherwise it returns 301 with the canonical location of the requested recordset.

    **Example request:**

    .. sourcecode:: http

        GET /v2/recordsets/f7b10e9b-0cae-4a91-b162-562bc6096648 HTTP/1.1
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

    :statuscode 301: Moved Permanently
    :statuscode 200: Success
    :statuscode 401: Access Denied

List Record Sets
----------------

**Lists all record sets for a given zone**

.. http:get:: /zones/(uuid:id)/recordsets

    **Example Request:**

    .. sourcecode:: http

        GET /v2/zones/c991f02b-ae05-4570-bf75-73def68fe700/recordsets HTTP/1.1
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
                    "status": "ACTIVE",
                    "description": null,
                    "links": {
                        "self": "http://127.0.0.1:9001/v2/zones/c991f02b-ae05-4570-bf75-73def68fe700/recordsets/29c5420e-8acb-4ef9-9aca-709a196c22dc"
                    },
                    "created_at": "2016-03-15T05:41:45.000000",
                    "updated_at": "2016-03-15T07:34:02.000000",
                    "records": [
                        "ns1.example.com. abc.example.com. 1458027242 3586 600 86400 3600"
                    ],
                    "zone_id": "c991f02b-ae05-4570-bf75-73def68fe700",
                    "version": 2,
                    "ttl": null,
                    "action": "NONE",
                    "type": "SOA",
                    "id": "29c5420e-8acb-4ef9-9aca-709a196c22dc",
                    "name": "example.org."
                },
                {
                   "status": "ACTIVE",
                   "description": null,
                   "links": {
                      "self": "http://127.0.0.1:9001/v2/zones/c991f02b-ae05-4570-bf75-73def68fe700/recordsets/7d80c4c6-e416-41d3-a29b-f408b9f51b8e"
                   },
                   "created_at": "2016-03-15T05:41:45.000000",
                   "updated_at": null,
                   "records": [
                       "ns1.example.com."
                   ],
                   "zone_id": "c991f02b-ae05-4570-bf75-73def68fe700",
                   "version": 1,
                   "ttl": null,
                   "action": "NONE",
                   "type": "NS",
                   "id": "7d80c4c6-e416-41d3-a29b-f408b9f51b8e",
                   "name": "example.org."
                },
                {
                   "status": "ACTIVE",
                   "description": "this is  an  example recordset",
                   "links": {
                       "self": "http://127.0.0.1:9001/v2/zones/c991f02b-ae05-4570-bf75-73def68fe700/recordsets/345e779d-90a4-4245-a460-42721a750e8c"
                   },
                   "created_at": "2016-03-15T07:34:02.000000",
                   "updated_at": null,
                   "records": ["10.1.0.2"],
                   "zone_id": "c991f02b-ae05-4570-bf75-73def68fe700",
                   "version": 1,
                   "ttl": null,
                   "action": "NONE",
                   "type": "A",
                   "id": "345e779d-90a4-4245-a460-42721a750e8c",
                   "name": "example.org."
                }
            ],
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/c991f02b-ae05-4570-bf75-73def68fe700/recordsets"
            },
            "metadata": {
                "total_count": 3
            }
        }


    :statuscode 200: Success
    :statuscode 401: Access Denied

**Lists record sets across all zones**

.. http:get:: /recordsets

    **Example Request:**

    .. sourcecode:: http

        GET /v2/recordsets HTTP/1.1
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
                    "ns1.devstack.org."
                ],
                "action": "NONE",
                "ttl": null,
                "status": "ACTIVE",
                "id": "65ee6b49-bb4c-4e52-9799-31330c94161f",
                "name": "example.org.",
                "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
                "zone_name": "example.org.",
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
                    "ns1.devstack.org. jli.ex.com. 1458666091 3502 600 86400 3600"
                ],
                "action": "NONE",
                "ttl": null,
                "status": "ACTIVE",
                "id": "14500cf9-bdff-48f6-b06b-5fc7491ffd9e",
                "name": "example.org.",
                "zone_id": "2150b1bf-dee2-4221-9d85-11f7886fb15f",
                "zone_name": "example.org.",
                "created_at": "2014-10-24T19:59:12.000000",
                "version": 1,
                "type": "SOA"
             },
             {
                "name": "example.com.",
                "id": "12caacfd-f0fc-4bcb-aa24-c42769897822",
                "type": "SOA",
                "zone_name": "example.com.",
                "action": "NONE",
                "ttl": null,
                "status": "ACTIVE",
                "description": null,
                "links": {
                    "self": "http://127.0.0.1:9001/v2/zones/b8d7eaf1-e5c7-4b15-be6e-4b2809f47ec3/recordsets/12caacfd-f0fc-4bcb-aa24-c42769897822"
                },
                "created_at": "2016-03-22T16:12:35.000000",
                "updated_at": "2016-03-22T17:01:31.000000",
                "records": [
                    "ns1.devstack.org. jli.ex.com. 1458666091 3502 600 86400 3600"
                ],
                "zone_id": "b8d7eaf1-e5c7-4b15-be6e-4b2809f47ec3",
                "version": 2
             },
             {
                "name": "example.com.",
                "id": "f39c51d1-ec2c-48a8-b9f7-877d56b7b82a",
                "type": "NS",
                "zone_name": "example.com.",
                "action": "NONE",
                "ttl": null,
                "status": "ACTIVE",
                "description": null,
                "links": {
                    "self": "http://127.0.0.1:9001/v2/zones/b8d7eaf1-e5c7-4b15-be6e-4b2809f47ec3/recordsets/f39c51d1-ec2c-48a8-b9f7-877d56b7b82a"
                },
                "created_at": "2016-03-22T16:12:35.000000",
                "updated_at": null,
                "records": [
                    "ns1.devstack.org."
                ],
                "zone_id": "b8d7eaf1-e5c7-4b15-be6e-4b2809f47ec3",
                "version": 1
             },
          ],
          "metadata": {
            "total_count": 4
          },
          "links": {
            "self": "https://127.0.0.1:9001/v2/recordsets"
          }
        }

**Filtering record sets**

.. http:get:: /recordsets?KEY=VALUE

    **Example Request:**

    .. sourcecode:: http

        GET /v2/recordsets?data=192.168* HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
          "metadata": {
            "total_count": 2
          },
          "links": {
            "self": "http://127.0.0.1:9001/v2/recordsets?data=192.168%2A"
          },
          "recordsets": [
            {
              "name": "mail.example.net.",
              "id": "a48588c5-5093-4585-b0fc-3e399d169c01",
              "type": "A",
              "zone_name": "example.net.",
              "action": "NONE",
              "ttl": null,
              "status": "ACTIVE",
              "description": null,
              "links": {
                "self": "http://127.0.0.1:9001/v2/zones/601a25f0-5c4d-4058-8d9c-e6a78f5ffbb8/recordsets/a48588c5-5093-4585-b0fc-3e399d169c01"
              },
              "created_at": "2016-04-04T20:11:08.000000",
              "updated_at": null,
              "records": [
                "192.168.0.1"
              ],
              "zone_id": "601a25f0-5c4d-4058-8d9c-e6a78f5ffbb8",
              "version": 1
            },
            {
              "name": "www.example.net.",
              "id": "f2c7a0f6-8ec7-4d14-b8ec-2a55a8129160",
              "type": "A",
              "zone_name": "example.net.",
              "action": "NONE",
              "ttl": null,
              "status": "ACTIVE",
              "description": null,
              "links": {
                "self": "http://127.0.0.1:9001/v2/zones/601a25f0-5c4d-4058-8d9c-e6a78f5ffbb8/recordsets/f2c7a0f6-8ec7-4d14-b8ec-2a55a8129160"
              },
              "created_at": "2016-04-04T22:21:03.000000",
              "updated_at": null,
              "records": [
                "192.168.6.6"
              ],
              "zone_id": "601a25f0-5c4d-4058-8d9c-e6a78f5ffbb8",
              "version": 1
            }
          ]
        }

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
    :statuscode 202: Accepted
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

        HTTP/1.1 202 Accepted

    :statuscode: 202 Accepted

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

    Creates a new SPF record set. SPF record set data formatting follows standard SPF record syntax.

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
