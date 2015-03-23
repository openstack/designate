.. _rest:

========================
 REST API Documentation
========================

Intro
=====

In the REST API examples, HTTP requests are defined as raw HTTP. For
example:

.. code-block:: http

   POST /v2/pools HTTP/1.1          # The HTTP Method, Path and HTTP Version
   Accept: application/json         # Headers
   Content-Type: application/json

   {                                # The rest is the body of request
        "name": "Example Pool",
        "ns_records": [
            {
              "hostname": "ns1.example.org.",
              "priority": 1
            }
        ]
   }

With this info we can make this request using the cURL_ tool. We'll
assume we are running Designate on `localhost`.

.. code-block:: bash

   curl -X POST -i \
        -H 'Accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{"name": "ns1.example.org."}' \
        http://localhost:9001/v1/servers

The `-i` flag is used to dump the response headers as well as the
response body.

The cURL tool is extremely robust. Please take a look at the `cURL
tutorial`_ for more info.

.. _cURL: http://curl.haxx.se/
.. _cURL tutorial: http://curl.haxx.se/docs/manual.html

API Versions
============

The API has 2 versions - V1 and V2.

V1 API
------
    .. toctree::
       :maxdepth: 2
       :glob:

       rest/v1/servers
       rest/v1/domains
       rest/v1/records
       rest/v1/diagnostics
       rest/v1/quotas
       rest/v1/reports
       rest/v1/sync

V2 API
------
    .. toctree::
       :maxdepth: 2
       :glob:

       rest/v2/collections
       rest/v2/zones
       rest/v2/recordsets
       rest/v2/tlds
       rest/v2/blacklists
       rest/v2/quotas
       rest/v2/pools

Admin API
---------
    .. toctree::
       :maxdepth: 2
       :glob:

       rest/admin/quotas

