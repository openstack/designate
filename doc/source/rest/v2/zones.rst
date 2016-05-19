..
    Copyright (C) 2014 eNovance SAS <licensing@enovance.com>

    Author: Artom Lifshitz <artom.lifshitz@enovance.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Zones
=====

A zone resource corresponds to the classical DNS zone.

Create Zone
-----------

.. http:post:: /zones

    Creates a new zone.

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "name": "example.org.",
            "email": "joe@example.org",
            "ttl": 7200,
            "description": "This is an example zone."
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.org.",
            "email": "joe@example.org",
            "ttl": 7200,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is an example zone.",
            "masters": [],
            "type": "PRIMARY",
            "transferred_at": null,
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
        }

    :form description: UTF-8 text field.
    :form name: Valid zone name (Immutable).
    :form type: Enum PRIMARY/SECONDARY, default PRIMARY (Immutable).
    :form email: email address, required for type PRIMARY, NULL for SECONDARY.
    :form ttl: time-to-live numeric value in seconds, NULL for SECONDARY.
    :form masters: Array of master nameservers. (NULL for type PRIMARY, required for SECONDARY otherwise zone will not be transferred before set).

    :statuscode 201: Created
    :statuscode 202: Accepted
    :statuscode 401: Access Denied

Get Zone
--------

.. http:get:: /zones/(uuid:id)

    Retrieves a zone with the specified zone ID.

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.org.",
            "email": "joe@example.org.",
            "ttl": 7200,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is an example zone.",
            "masters": [],
            "type": "PRIMARY",
            "transferred_at": null,
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

Get Zone Name Servers
---------------------

.. http:get:: /zones/(uuid:id)/nameservers

    Retrieves the nameservers for a zone with zone_id of id

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3/nameservers HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
            "nameservers": [
                {
                    "hostname": "ns1.example.com.",
                    "priority": 1
                },
                {
                    "hostname": "ns2.example.com.",
                    "priority": 2
                }
            ]
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

List Zones
----------

.. http:get:: /zones

    Lists all zones.

    **Example Request:**

    .. sourcecode:: http

        GET /v2/zones HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
          "zones": [{
            "status": "ACTIVE",
            "masters": [],
            "name": "example.org.",
            "links": {
              "self": "http://127.0.0.1:9001/v2/zones/c991f02b-ae05-4570-bf75-73def68fe700"
            },
            "transferred_at": null,
            "created_at": "2016-03-15T05:41:45.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-15T05:41:50.000000",
            "version": 2,
            "id": "c991f02b-ae05-4570-bf75-73def68fe700",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1458020505,
            "project_id": "6b89012cdb2640c3a80b8d777d9bac16",
            "type": "PRIMARY",
            "email": "abc@example.com",
            "description": null
          },
          {
            "status": "ACTIVE",
            "masters": [],
            "name": "example1.org.",
            "links": {
              "self": "http://127.0.0.1:9001/v2/zones/0d35ce4e-f3b4-4ba7-9b94-4f9eba49018a"
            },
            "transferred_at": null,
            "created_at": "2016-03-15T05:54:24.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-15T05:54:44.000000",
            "version": 2,
            "id": "0d35ce4e-f3b4-4ba7-9b94-4f9eba49018a",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1458021264,
            "project_id": "6b89012cdb2640c3a80b8d777d9bac16",
            "type": "PRIMARY",
            "email": "abc@example.com",
            "description": null
          }],
          "links": {
            "self": "http://127.0.0.1:9001/v2/zones"
            },
          "metadata": {
            "total_count": 2
            }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

Update Zone
-----------

.. http:patch:: /zones/(uuid:id)

    Changes the specified attribute(s) for an existing zone.

    In the example below, we update the TTL to 3600.

    **Request:**

    .. sourcecode:: http

        PATCH /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "ttl": 3600
        }

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.org.",
            "email": "joe@example.org.",
            "ttl": 3600,
            "serial": 1404760160,
            "status": "ACTIVE",
            "description": "This is an example zone.",
            "masters": [],
            "type": "PRIMARY",
            "transferred_at": null,
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": "2014-07-07T19:09:20.876366",
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
        }

    :form description: UTF-8 text field.
    :form name: Valid zone name (Immutable).
    :form type: Enum PRIMARY/SECONDARY, default PRIMARY (Immutable).
    :form email: email address, required for type PRIMARY, NULL for SECONDARY.
    :form ttl: time-to-live numeric value in seconds, NULL for SECONDARY
    :form masters: Array of master nameservers. (NULL for type PRIMARY, required for SECONDARY otherwise zone will not be transferred before set.)

    :statuscode 200: Success
    :statuscode 202: Accepted
    :statuscode 401: Access Denied

Delete Zone
-----------

.. http:delete:: zones/(uuid:id)

    Deletes a zone with the specified zone ID. Deleting a zone is asynchronous.
    Once pool manager has deleted the zone from all the pool targets, the zone
    is deleted from storage.

    **Example Request:**

    .. sourcecode:: http

        DELETE /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 202 Accepted

    :statuscode 202: Accepted


Abandon Zone
------------

.. http:post:: /zones/(uuid:id)/tasks/abandon

    When a zone is abandoned it removes the zone from Designate's storage.
    There is no operation done on the pool targets. This is intended to be used
    in the cases where Designate's storage is incorrect for whatever reason. By
    default this is restricted by policy (abandon_domain) to admins.

    **Example Request:**

    .. sourcecode:: http

        POST /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3/tasks/abandon HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 204 No content

    :statuscode 204: No content

Transfer Zone
-------------

Create Zone Transfer Request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:post:: /zones/(uuid:id)/tasks/transfer_requests

    To initiate a transfer the original owner must create a transfer request.

    This will return two items that are required to continue:
        * key: a password that is used to validate the transfer
        * id: ID of the request.

    Both of these should be communicated out of band (email / IM / etc) to the intended recipient

    There is an option of limiting the transfer to a single project. If that is required, the person initiating the transfer
    will need the Project ID. This will also allow the targeted project to see the transfer in their list of requests.

    A non-targeted request will not show in a list operation, apart from the owning projects request.
    An targeted request will only show in the targets and owners lists.

    An untargeted request can be viewed by any authenticated user.

    **Example Request**

    .. sourcecode:: http

        POST /v2/zones/6b78734a-aef1-45cd-9708-8eb3c2d26ff8/tasks/transfer_requests HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "target_project_id": "123456",
            "description": "Transfer qa.dev.example.com. to QA Team"
        }

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "created_at": "2014-07-17T20:34:40.882579",
            "description": null,
            "id": "f2ad17b5-807a-423f-a991-e06236c247be",
            "key": "9Z2R50Y0",
            "project_id": "1",
            "status": "ACTIVE",
            "target_project_id": "123456",
            "updated_at": null,
            "zone_id": "6b78734a-aef1-45cd-9708-8eb3c2d26ff8",
            "zone_name": "qa.dev.example.com.",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_requests/f2ad17b5-807a-423f-a991-e06236c247be"
            }
        }

    :form description: UTF-8 text field
    :form target_project_id: Optional field to only allow a single tenant to accept the transfer request


List Zone Transfer Requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:get:: /zones/tasks/transfer_requests

    List all transfer requests that the requesting project have created, or are targeted to that project

    The detail shown will differ, based on who the requester is.

    **Example Request**

    .. sourcecode:: http

        GET /zones/tasks/transfer_requests HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "transfer_requests": [
                {
                    "created_at": "2014-07-17T20:34:40.882579",
                    "description": "This was created by the requesting project",
                    "id": "f2ad17b5-807a-423f-a991-e06236c247be",
                    "key": "9Z2R50Y0",
                    "project_id": "1",
                    "status": "ACTIVE",
                    "target_project_id": "123456",
                    "updated_at": null,
                    "zone_id": "6b78734a-aef1-45cd-9708-8eb3c2d26ff8",
                    "zone_name": "qa.dev.example.com.",
                    "links": {
                        "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_requests/f2ad17b5-807a-423f-a991-e06236c247be"
                    }
                },
                {
                    "description": "This is scoped to the requesting project",
                    "id": "efd2d720-b0c4-43d4-99f7-d9b53e08860d",
                    "zone_id": "2c4d5e37-f823-4bee-9859-031cb44f80e7",
                    "zone_name": "subdomain.example.com.",
                    "status": "ACTIVE",
                    "links": {
                        "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_requests/efd2d720-b0c4-43d4-99f7-d9b53e08860d"
                    }
                }
            ],
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_requests"
            }
        }


View a Transfer Request
^^^^^^^^^^^^^^^^^^^^^^^

.. http:get:: /zones/tasks/transfer_requests/(uuid:id)

    Show details about a request.

    This allows a user to view a transfer request before accepting it

    **Example Request**

    .. sourcecode:: http

        GET /v2/zones/tasks/transfer_requests/f2ad17b5-807a-423f-a991-e06236c247be HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "description": "This is scoped to the requesting project",
            "id": "efd2d720-b0c4-43d4-99f7-d9b53e08860d",
            "zone_id": "2c4d5e37-f823-4bee-9859-031cb44f80e7",
            "zone_name": "subdomain.example.com.",
            "status": "ACTIVE",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_requests/efd2d720-b0c4-43d4-99f7-d9b53e08860d"
            }
        }


Update a Transfer Request
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http: patch:: /zones/tasks/transfer_requests/(uuid:id)

    Update a transfer request.

    This allows a user to update a transfer request before accepting it.

    **Example Request**

    .. sourcecode:: http

       PATCH v2/zones/tasks/transfer_requests/b853202b-22f9-49c1-893d-49cbbf6830bb HTTP/1.1
       Host: 127.0.0.1:9001
       Accept: application/json
       Content: application/json

       {
         "description": "demo_transfer"
       }

    **Example Response**

    ..sourcecode:: http

      HTTP/1.1 200 OK
      Content-Length: 476
      Content-Type: application/json
      charset=UTF-8

      {
          "status": "ACTIVE",
          "target_project_id": dc685ea10a3a4ddfb9bc2deeca66f131,
          "zone_id": "08615081-cbfd-445e-9d35-15fccf2be4be",
          "links": {
               "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_requests/b853202b-22f9-49c1-893d-49cbbf6830bb"
          },
          "created_at": "2016-01-28T04:43:00.000000",
          "updated_at": "2016-01-28T04:45:17.000000",
          "key": "XWUR5VFL",
          "zone_name": "example.com.",
          "project_id": "dc685ea10a3a4ddfb9bc2deeca66f131",
          "id": "b853202b-22f9-49c1-893d-49cbbf6830bb",
          "description": "demo_transfer"
    }

    :statuscode 200: Success
    :statuscode 202: Accepted
    :statuscode 401: Access Denied

    :form description: UTF-8 text field


Delete a transfer request
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http: delete:: /zones/tasks/transfer_requests/(uuid:id)

    Delete a zone transfer request with the specified id.

    **Example Request**

    .. sourcecode:: http

       DELETE  /v2/zones/tasks/transfer_requests/"b853202b-22f9-49c1-893d-49cbbf6830bb HTTP/1.1
       Host: 127.0.0.1:9001
       Accept: application/json
       Content: application/json

    **Example Response**

    .. sourcecode:: http

       HTTP/1.1 204 No Content

    :statuscode 204: No Content


Accept a Transfer Request
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:post:: /zones/tasks/transfer_accepts

    Accept a zone transfer request. This is called by the project that will own the zone
    (i.e. the project that will maintain the zone)

    Once the API returns "Complete" the zone has been transferred to the new project

    **Example Request**

    .. sourcecode:: http

        POST /v2/zones/tasks/transfer_accepts HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "key":"J6JCET2C",
            "zone_transfer_request_id":"98ba1d22-c092-4603-891f-8a0ab04f7e57"
        }

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Length: 532
        Content-Type: application/json
        charset=UTF-8

        {
            "status": "COMPLETE",
            "zone_id": "53cdcf82-9e32-4a00-a90d-32d6ec5db7e9",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_accepts/46b04776-a7c9-45b4-812e-b8e615d1d73b",
                "zone": "http://127.0.0.1:9001/v2/zones/53cdcf82-9e32-4a00-a90d-32d6ec5db7e9"
            },
            "created_at": "2016-05-13 08:01:16",
            "updated_at": "2016-05-13 08:01:16",
            "key": "J6JCET2C",
            "project_id": "10457ad1fe074f4a89bb1e4c0cd83d40",
            "id": "46b04776-a7c9-45b4-812e-b8e615d1d73b",
            "zone_transfer_request_id": "98ba1d22-c092-4603-891f-8a0ab04f7e57"
        }


View a Transfer Accept
^^^^^^^^^^^^^^^^^^^^^^

.. http:get:: /zones/tasks/transfer_accepts/(uuid:id)

    **Example Request**

    .. sourcecode:: http

        GET /v2/zones/tasks/transfer_accepts/46b04776-a7c9-45b4-812e-b8e615d1d73b HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Length: 526
        Content-Type: application/json
        charset=UTF-8

        {
            "status": "COMPLETE",
            "zone_id": "53cdcf82-9e32-4a00-a90d-32d6ec5db7e9",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_accepts/46b04776-a7c9-45b4-812e-b8e615d1d73b",
                "zone": "http://127.0.0.1:9001/v2/zones/53cdcf82-9e32-4a00-a90d-32d6ec5db7e9"
            },
            "created_at": "2016-05-13 08:01:16",
            "updated_at": "2016-05-13 08:01:16",
            "key": null,
            "project_id": "10457ad1fe074f4a89bb1e4c0cd83d40",
            "id": "46b04776-a7c9-45b4-812e-b8e615d1d73b",
            "zone_transfer_request_id": "98ba1d22-c092-4603-891f-8a0ab04f7e57"
        }


Import Zone
-----------

Create a Zone Import
^^^^^^^^^^^^^^^^^^^^

.. http:post:: /zones/tasks/imports

    To import a zonefile, set the Content-type to **text/dns** . The
    **zoneextractor.py** tool in the **contrib** folder can generate zonefiles
    that are suitable for Designate (without any **$INCLUDE** statements for
    example).

    An object will be returned that can be queried using the 'self' link the
    'links' field.

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones/tasks/imports HTTP/1.1
        Host: 127.0.0.1:9001
        Content-type: text/dns

        $ORIGIN example.com.
        example.com. 42 IN SOA ns.example.com. nsadmin.example.com. 42 42 42 42 42
        example.com. 42 IN NS ns.example.com.
        example.com. 42 IN MX 10 mail.example.com.
        ns.example.com. 42 IN A 10.0.0.1
        mail.example.com. 42 IN A 10.0.0.2

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "status": "PENDING",
            "zone_id": null,
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/imports/074e805e-fe87-4cbb-b10b-21a06e215d41"
            },
            "created_at": "2015-05-08T15:43:42.000000",
            "updated_at": null,
            "version": 1,
            "message": null,
            "project_id": "1",
            "id": "074e805e-fe87-4cbb-b10b-21a06e215d41"
        }

    :statuscode 202: Accepted
    :statuscode 415: Unsupported Media Type


View a Zone Import
^^^^^^^^^^^^^^^^^^

.. http:get:: /zones/tasks/imports/(uuid:id)

    The status of a zone import can be viewed by querying the id
    given when the request was created.

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/tasks/imports/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status": "COMPLETE",
            "zone_id": "6625198b-d67d-47dc-8d29-f90bd60f3ac4",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/imports/074e805e-fe87-4cbb-b10b-21a06e215d41",
                "href": "http://127.0.0.1:9001/v2/zones/6625198b-d67d-47dc-8d29-f90bd60f3ac4"
            },
            "created_at": "2015-05-08T15:43:42.000000",
            "updated_at": "2015-05-08T15:43:42.000000",
            "version": 2,
            "message": "example.com. imported",
            "project_id": "noauth-project",
            "id": "074e805e-fe87-4cbb-b10b-21a06e215d41"
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied
    :statuscode 404: Not Found

    Notice the status has been updated, the message field shows that the zone was
    successfully imported, and there is now a 'href' in the 'links' field that points
    to the new zone.

List Zone Imports
^^^^^^^^^^^^^^^^^

.. http:get:: /zones/tasks/imports/

    List all of the zone imports created by this project.

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/tasks/imports/ HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
             "imports": [
                 {
                    "status": "COMPLETE",
                    "zone_id": 047888ee-e9dd-4c08-8b44-ab2e879e01bd,
                    "links": {
                        "self": "http://127.0.0.1:9001/v2/zones/tasks/imports/0436a86e-ffc1-4d38-82a7-d75170fcd2a9",
                        "href": "http://127.0.0.1:9001/v2/zones/047888ee-e9dd-4c08-8b44-ab2e879e01bd"
                    },
                    "created_at": "2016-04-05T06:03:06.000000",
                    "updated_at": "2016-04-05T06:03:06.000000",
                    "version": 2,
                    "message": "example.com. imported",
                    "project_id": "1de6e2fdc22342d3bef6340c7b70f497",
                    "id": "0436a86e-ffc1-4d38-82a7-d75170fcd2a9"
                },
                {
                    "status": "COMPLETE",
                    "zone_id": 68a17870-7f81-470a-b5e9-2753460fd6dc,
                    "links": {
                        "self": "http://127.0.0.1:9001/v2/zones/tasks/imports/f0aa4ac1-f975-46a4-b417-339acd1ea8e3",
                        "href": "http://127.0.0.1:9001/v2/zones/68a17870-7f81-470a-b5e9-2753460fd6dc"
                    },
                    "created_at": "2016-04-05T06:06:26.000000",
                    "updated_at": "2016-04-05T06:06:26.000000",
                    "version": 2,
                    "message": "temp.org. imported",
                    "project_id": "1de6e2fdc22342d3bef6340c7b70f497",
                    "id": "f0aa4ac1-f975-46a4-b417-339acd1ea8e3"
                }
             ],
             "links": {
                 "self": "http://127.0.0.1:9001/v2/zones/tasks/imports"
             },
             "metadata": {
                 "total_count": 2
             }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied
    :statuscode 404: Not Found

Delete Zone Import
^^^^^^^^^^^^^^^^^^

.. http:delete:: /zones/tasks/imports/(uuid:id)

    Deletes a zone import with the specified ID. This does not affect the zone
    that was imported, it simply removes the record of the import.

    **Example Request:**

    .. sourcecode:: http

        DELETE /v2/zones/tasks/imports/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 204 No Content

    :statuscode 204: No Content

Export Zone
-----------

Create a Zone Export
^^^^^^^^^^^^^^^^^^^^

.. http:post:: /zones/(uuid:id)/tasks/export

    To export a zone in BIND9 zonefile format, a zone export resource must be
    created. This is accomplished by initializing an export task.

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones/074e805e-fe87-4cbb-b10b-21a06e215d41/tasks/export HTTP/1.1
        Host: 127.0.0.1:9001

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 202 Accepted
        Content-Type: application/json

        {
            "status": "PENDING",
            "zone_id": "074e805e-fe87-4cbb-b10b-21a06e215d41",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/exports/8ec17fe1-d1f9-41b4-aa98-4eeb4c27b720"
            },
            "created_at": "2015-08-27T20:57:03.000000",
            "updated_at": null,
            "version": 1,
            "location": null,
            "message": null,
            "project_id": "1",
            "id": "8ec17fe1-d1f9-41b4-aa98-4eeb4c27b720"
        }

    :statuscode 202: Accepted

View a Zone Export Record
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:get:: /zones/tasks/exports/(uuid:id)

    The status of a zone export can be viewed by querying the id
    given when the request was created.

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/tasks/exports/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status": "COMPLETE",
            "zone_id": "6625198b-d67d-47dc-8d29-f90bd60f3ac4",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/exports/8ec17fe1-d1f9-41b4-aa98-4eeb4c27b720",
                "export": "http://127.0.0.1:9001/v2/zones/tasks/exports/8ec17fe1-d1f9-41b4-aa98-4eeb4c27b720/export"
            },
            "created_at": "2015-08-27T20:57:03.000000",
            "updated_at": "2015-08-27T20:57:03.000000",
            "version": 2,
            "location": "designate://v2/zones/tasks/exports/8ec17fe1-d1f9-41b4-aa98-4eeb4c27b720/export",
            "message": null,
            "project_id": "noauth-project",
            "id": "8ec17fe1-d1f9-41b4-aa98-4eeb4c27b720"
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied
    :statuscode 404: Not Found

    Notice the status has been updated and there is now an 'export' in the 'links' field that points
    to a link where the export (zonefile) can be accessed.


View the Exported Zone
^^^^^^^^^^^^^^^^^^^^^^

The link that is generated in the export field in an export resource can be followed to
a Designate resource, or an external resource. If the link is to a Designate endpoint, the
zonefile can be retrieved directly through the API by following that link.

.. http:get:: /zones/tasks/exports/(uuid:id)

    **Example request:**

    .. sourcecode:: http

        GET /zones/tasks/exports/8ec17fe1-d1f9-41b4-aa98-4eeb4c27b720/export HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: text/dns


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: text/dns

        $ORIGIN example.com.
        $TTL 42

        example.com. IN SOA ns.designate.com. nsadmin.example.com. (
            1394213803 ; serial
            3600 ; refresh
            600 ; retry
            86400 ; expire
            3600 ; minimum
        )


        example.com. IN NS ns.designate.com.


        example.com.  IN MX 10 mail.example.com.
        ns.example.com.  IN A  10.0.0.1
        mail.example.com.  IN A  10.0.0.2

    :statuscode 200: Success
    :statuscode 401: Access Denied
    :statuscode 404: Not Found

    Notice how the SOA and NS records are replaced with the Designate server(s).

List Zone Exports
^^^^^^^^^^^^^^^^^

.. http:get:: /zones/tasks/exports/

    List all of the zone exports created by this project.

    **Example request:**

    .. sourcecode:: http

        GET /v2/zones/tasks/exports/ HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {

            "exports": [
                {
                    "status": "COMPLETE",
                    "zone_id": "17a8d6b3-6ace-4857-b113-a707c5f975b1",
                    "links": {
                        "self": "http://127.0.0.1:9001/v2/zones/tasks/exports/204be410-0a9c-44b8-839e-bc4df3bb0d9a",
                        "export": "http://127.0.0.1:9001/v2/zones/tasks/exports/204be410-0a9c-44b8-839e-bc4df3bb0d9a/export"
                    },
                    "created_at": "2016-04-04T01:53:29.000000",
                    "updated_at": "2016-04-04T01:53:29.000000",
                    "version": 2,
                    "location": "designate://v2/zones/tasks/exports/204be410-0a9c-44b8-839e-bc4df3bb0d9a/export",
                    "message": null,
                    "project_id": "1de6e2fdc22342d3bef6340c7b70f497",
                    "id": "204be410-0a9c-44b8-839e-bc4df3bb0d9a"
                }
            ],
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/exports"
            },
            "metadata": {
                "total_count": 1
            }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied
    :statuscode 404: Not Found

Delete Zone Export
^^^^^^^^^^^^^^^^^^

.. http:delete:: /zones/tasks/exports/(uuid:id)

    Deletes a zone export with the specified ID. This does not affect the zone
    that was exported, it simply removes the record of the export. If the link
    to view the export was pointing to a Designate API endpoint, the endpoint
    will no longer be available.

    **Example Request:**

    .. sourcecode:: http

        DELETE /v2/zones/tasks/exports/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 204 No Content

    :statuscode 204: No Content
