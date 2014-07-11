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
          "zone": {
            "name": "example.org.",
            "email": "joe@example.org",
            "ttl": 7200,
            "description": "This is an example zone."
          }
        }

    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
          "zone": {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.org.",
            "email": "joe@example.org",
            "ttl": 7200,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is an example zone.",
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
          }
        }

    :form description: UTF-8 text field
    :form email: email address
    :form name: zone name
    :form ttl: time-to-live numeric value in seconds

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
          "zone": {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.org.",
            "email": "joe@example.org.",
            "ttl": 7200,
            "serial": 1404757531,
            "status": "ACTIVE",
            "description": "This is an example zone.",
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": null,
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
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
          "zone": {
            "ttl": 3600
          }
        }

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "zone": {
            "id": "a86dba58-0043-4cc6-a1bb-69d5e86f3ca3",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "project_id": "4335d1f0-f793-11e2-b778-0800200c9a66",
            "name": "example.org.",
            "email": "joe@example.org.",
            "ttl": 3600,
            "serial": 1404760160,
            "status": "ACTIVE",
            "description": "This is an example zone.",
            "version": 1,
            "created_at": "2014-07-07T18:25:31.275934",
            "updated_at": "2014-07-07T19:09:20.876366",
            "links": {
              "self": "https://127.0.0.1:9001/v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3"
            }
          }
        }

    :form description: UTF-8 text field
    :form email: email address
    :form name: zone name
    :form ttl: time-to-live numeric value in seconds

    :statuscode 200: Success
    :statuscode 202: Accepted
    :statuscode 401: Access Denied

Delete Zone
-----------

.. http:delete:: zones/(uuid:id)

    Deletes a zone with the specified zone ID.

    **Example Request:**

    .. sourcecode:: http

        DELETE /v2/zones/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

    **Example Response:**

    .. sourcecode:: http

        HTTP/1.1 204 No Content

    :statuscode 204: No content

Import Zone
-----------

.. http:post:: /zones

    To import a zonefile, set the Content-type to **text/dns**. The
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
            "zone": {
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
                "version": 1
            }
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
