Zones
=====

Overview
--------
The zones extension can be used to export zonesfiles from designate.

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
