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

Import
------

.. http:post:: /zones

    To import a zonefile, set the Content-type to **text/dns**. The
    **zoneextractor.py** tool in the **contrib** folder can generate zonefiles
    that are suitable for Designate (without any **$INCLUDE** statements for
    example).

    **Example request**

    .. sourcecode:: http

        POST /zones HTTP/1.1
        Host: 127.0.0.1:9001
        Content-type: text/dns

        $ORIGIN example.com.
        example.com. 42 IN SOA ns.example.com. nsadmin.example.com. 42 42 42 42 42
        example.com. 42 IN NS ns.example.com.
        example.com. 42 IN MX 10 mail.example.com.
        ns.example.com. 42 IN A 10.0.0.1
        mail.example.com. 42 IN A 10.0.0.2

    **Example response**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
            "zone": {
                "created_at": "2014-03-07T17:36:40.349001",
                "description": null,
                "email": "nsadmin@example.com",
                "id": "6b78734a-aef1-45cd-9708-8eb3c2d26ff1",
                "links": {
                    "self": "http://127.0.0.1:9001/v2/zones/6b78734a-aef1-45cd-9708-8eb3c2d26ff1"
                },
                "name": "example.com.",
                "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
                "project_id": "d7accc2f8ce343318386886953f2fc6a",
                "serial": 1394213800,
                "ttl": "42",
                "updated_at": null,
                "version": 1
            }
        }

    :form created_at: timestamp
    :form updated_at: timestamp
    :form description: UTF-8 text field
    :form email: email address
    :form id: UUID
    :form links: JSON object
    :form name: zone name
    :form pool_id: UUID
    :form project_id: UUID
    :form serial: numeric seconds
    :form ttl: time-to-live numeric value in seconds
    :form version: version number
    :statuscode 201: Created
    :statuscode 415: Unsupported Media Type
    :statuscode 400: Bad request

Export
------

.. http:get:: /zones/(uuid:id)

    To export a zone in zonefile format, set the **Accept** header to **text/dns**.

    **Example request**

    .. sourcecode:: http

        GET /zones/6b78734a-aef1-45cd-9708-8eb3c2d26ff1 HTTP/1.1
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
