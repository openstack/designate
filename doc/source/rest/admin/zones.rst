Zones
=====

Overview
--------
The zones extension can be used to import and export zonesfiles to designate.

*Note*: Zones is an extension and needs to be enabled before it can be used.
If Designate returns a 404 error, ensure that the following line has been
added to the designate.conf file::

    enabled_extensions_admin = zones

Once this line has been added, restart the designate-api service.

Export Zone
-----------

.. http:get:: /admin/zones/export/(uuid:id)

    **Example request:**

    .. sourcecode:: http

        GET /admin/zones/export/a86dba58-0043-4cc6-a1bb-69d5e86f3ca3 HTTP/1.1
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
    :statuscode 406: Not Acceptable

    Notice how the SOA and NS records are replaced with the Designate server(s).

Import Zone
-----------

.. http:post:: /admin/zones/import

    To import a zonefile, set the Content-type to **text/dns** . The
    **zoneextractor.py** tool in the **contrib** folder can generate zonefiles
    that are suitable for Designate (without any **$INCLUDE** statements for
    example).

    **Example request:**

    .. sourcecode:: http

        POST /admin/zones/import HTTP/1.1
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
