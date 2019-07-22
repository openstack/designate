.. _rest:

=================================
Deprecated REST API Documentation
=================================

Intro
=====

In the REST API examples, HTTP requests are defined as raw HTTP. For
example:

.. code-block:: http

   POST /v2/zones HTTP/1.1
   Accept: application/json
   Content-Type: application/json

   {
        "name": "example.org.",
        "email": "hostmaster@example.org"
   }

With this info we can make this request using the cURL_ tool. We'll
assume we are running Designate on `localhost`.

.. code-block:: bash

   curl -X POST -i \
        -H 'Accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{"name": "example.org.", "email": "hostmaster@example.org"}' \
        http://localhost:9001/v2/zones

The `-i` flag is used to dump the response headers as well as the
response body.

The cURL tool is extremely robust. Please take a look at the `cURL
tutorial`_ for more info.

.. _cURL: http://curl.haxx.se/
.. _cURL tutorial: http://curl.haxx.se/docs/manual.html

HTTP Headers
============

These headers work for all APIs

* X-Designate-Edit-Managed-Records
    - Allows admins (or users with the right role) to modify managed records
      (records created by designate-sink / reverse floating ip API)
* X-Auth-All-Projects
    - Allows admins (or users with the right role) to view and edit
      zones / recordsets for all tenants
* X-Auth-Sudo-Tenant-ID / X-Auth-Sudo-Project-ID
    - Allows admins (or users with the right role) to impersonate another
      tenant specified by this header

API Versions
============

V2 API
------

    The V2 API is documented on the OpenStack Developer `api site`_


Admin API
---------
    .. toctree::
       :maxdepth: 2
       :glob:

       rest/admin/quotas

.. _api site: https://docs.openstack.org/api-ref/dns/
