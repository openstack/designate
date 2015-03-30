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
          }, {
            "id": "fdd7b0dc-52a3-491e-829f-41d18e1d3ada",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.net.",
            "email": "joe@example.net.",
            "ttl": 7200,
            "serial": 1404756682,
            "status": "ACTIVE",
            "description": "This is another example zone.",
            "masters": [],
            "type": "PRIMARY",
            "transferred_at": null,
            "version": 1,
            "created_at": "2014-07-07T18:22:08.287743",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/fdd7b0dc-52a3-491e-829f-41d18e1d3ada"
            }
          }],
          "links": {
            "self": "https://127.0.0.1:9001/v2/zones"
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

Import Zone
-----------

.. http:post:: /zones

    To import a zonefile, set the Content-type to **text/dns** . The
    **zoneextractor.py** tool in the **contrib** folder can generate zonefiles
    that are suitable for Designate (without any **$INCLUDE** statements for
    example).

    **Example request:**

    .. sourcecode:: http

        POST /v2/zones HTTP/1.1
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
            "email": "nsadmin@example.com",
            "id": "6b78734a-aef1-45cd-9708-8eb3c2d26ff1",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/6b78734a-aef1-45cd-9708-8eb3c2d26ff1"
            },
            "name": "example.com.",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "d7accc2f8ce343318386886953f2fc6a",
            "serial": 1404757531,
            "ttl": "42",
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "version": 1,
            "masters": [],
            "type": "PRIMARY",
            "transferred_at": null
        }

    :statuscode 201: Created
    :statuscode 415: Unsupported Media Type
    :statuscode 400: Bad request

Export Zone
-----------

.. http:get:: /zones/(uuid:id)

    To export a zone in zonefile format, set the **Accept** header to **text/dns**.

    **Example request**

    .. sourcecode:: http

        GET /v2/zones/6b78734a-aef1-45cd-9708-8eb3c2d26ff1 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: text/dns

    **Example response**

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
    :statuscode 406: Not Acceptable

    Notice how the SOA and NS records are replaced with the Designate server(s).

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

    An un-targeted request can be viewed by any authenticated user.

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


Accept a Transfer Request
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:post:: /zones/tasks/transfer_accepts

    Accept a zone transfer request. This is called by the project that will own the zone
    (i.e. the project that will maintain the zone)

    Once the API returns "Complete" the zone has been transferred to the new project

    **Example Request**

    .. sourcecode:: http

        POST /v2/zones/tasks/transfer_accept HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
            "key":"9Z2R50Y0",
            "zone_transfer_request_id":"f2ad17b5-807a-423f-a991-e06236c247be"
        }

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "id": "581891d5-99f5-49e1-86c3-eec0f44d66fd",
            "links": {
                "self": "http://127.0.0.1:9001/v2/zones/tasks/transfer_accepts/581891d5-99f5-49e1-86c3-eec0f44d66fd",
                "zone": "http://127.0.0.1:9001/v2/zones/6b78734a-aef1-45cd-9708-8eb3c2d26ff8"
            },
            "status": "COMPLETE"
        }

