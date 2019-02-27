..
    Copyright 2015 Rackspace Hosting

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


==========================
 How To Manage PTR Records
==========================


PTR Record Basics
=================

`PTR` records provide a reverse mapping from a single IP or set of IP
addresses to a domain. For example,

.. code-block:: bash

   $ dig -x 192.0.2.12 +short
   example.org.

The way this works in the DNS system is through the `in-addr.arpa.`
zone. For example

.. code-block:: bash

   $ dig example.org +short
   192.0.2.12
   $ dig -x 192.0.2.12
   ; <<>> DiG 9.9.5-3ubuntu0.1-Ubuntu <<>> -x 192.0.2.12
   ;; global options: +cmd
   ;; Got answer:
   ;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 3431
   ;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 1, ADDITIONAL: 1

   ;; OPT PSEUDOSECTION:
   ; EDNS: version: 0, flags:; udp: 4000
   ;; QUESTION SECTION:
   ;12.2.0.192.in-addr.arpa.   IN      PTR      example.org.

   ;; AUTHORITY SECTION:
   12.2.0.192.in-addr.arpa. 3600 IN     NS      ns1.example.org.

   ;; Query time: 40 msec
   ;; SERVER: 127.0.0.1#53(127.0.0.1)
   ;; WHEN: Fri Feb 20 19:05:44 UTC 2015
   ;; MSG SIZE  rcvd: 119

In the question section we see the address being requested from the
DNS system as `12.2.0.192.in-addr.arpa.`. As you can see, the IP
address has been reversed in order to function similarly to a domain
name where the more specific elements come first. The reversed IP
address is then added to the `in-addr.arpa.` domain, at which point
the DNS system can perform a simple look up to find any `PTR` records
that describe what domain name, if any, maps to that IP.


Create a PTR Record in Designate
================================

To create a `PTR` record in Designate, there are two requirements.

 1. A domain that should be pointed to from the IP
 2. A `in-addr.arpa.` zone entry that will receive the actual `PTR`
    record


Using the V2 API
----------------

To begin let's create a zone that we want to return when we do our
reverse lookup.

.. code-block:: http

  POST /v2/zones HTTP/1.1
  Accept: application/json
  Content-Type: application/json

  {
    "name": "example.org.",
    "email": "admin@example.org",
    "ttl": 3600,
    "description": "A great example zone"
  }


Here is the JSON response describing the new zone.

.. code-block:: http

  HTTP/1.1 202 Accepted
  Location: http://127.0.0.1:9001/v2/zones/fe078042-0aa3-4500-a81e-8f328f79bf75
  Content-Length: 476
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-bfcd0723-624c-4ec2-bbd5-99e985efe8db
  Date: Fri, 20 Feb 2015 21:20:28 GMT
  Connection: keep-alive

  {
    "email": "admin@example.org",
    "project_id": "noauth-project",
    "action": "CREATE",
    "version": 1,
    "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
    "created_at": "2015-02-20T21:20:28.000000",
    "name": "example.org.",
    "id": "fe078042-0aa3-4500-a81e-8f328f79bf75",
    "serial": 1424467228,
    "ttl": 3600,
    "updated_at": null,
    "links": {
      "self": "http://127.0.0.1:9001/v2/zones/fe078042-0aa3-4500-a81e-8f328f79bf75"
    },
    "description": "A great example zone",
    "status": "PENDING"
  }

.. note::
   The `status` is `PENDING`. If we make a `GET` request to
   the `self` field in the zone, it will most likely have been
   processed and updated to `ACTIVE`.

Now that we have a zone we'd like to use for our reverse DNS lookup,
we need to add an `in-addr.arpa.` zone that includes the IP address
we'll be looking up.

Let's configure `192.0.2.11` to return our `example.org.` domain
name when we do a reverse look up.

.. code-block:: http

  POST /v2/zones HTTP/1.1
  Accept: application/json
  Content-Type: application/json

  {
    "name": "11.2.0.192.in-addr.arpa.",
    "email": "admin@example.org",
    "ttl": 3600,
    "description": "A in-addr.arpa. zone for reverse lookups."
  }

As you can see, in the `name` field we've reversed our IP address and
used that as a subdomain in the `in-addr.arpa.` zone.

Here is the response.

.. code-block:: http

  HTTP/1.1 202 Accepted
  Location: http://127.0.0.1:9001/v2/zones/1bed5d24-d487-4410-b813-f1c637db0ba3
  Content-Length: 512
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-4e691123-045e-4f8e-ae50-b5eabb5af3fa
  Date: Fri, 20 Feb 2015 21:35:41 GMT
  Connection: keep-alive

  {
    "email": "admin@example.org",
    "project_id": "noauth-project",
    "action": "CREATE",
    "version": 1,
    "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
    "created_at": "2015-02-20T21:35:41.000000",
    "name": "11.2.0.192.in-addr.arpa.",
    "id": "1bed5d24-d487-4410-b813-f1c637db0ba3",
    "serial": 1424468141,
    "ttl": 3600,
    "updated_at": null,
    "links": {
      "self": "http://127.0.0.1:9001/v2/zones/1bed5d24-d487-4410-b813-f1c637db0ba3"
    },
    "description": "A in-addr.arpa. zone for reverse lookups.",
    "status": "PENDING"
  }

Now that we have our `in-addr.arpa.` zone, we add a new `PTR` record
to the zone.

.. code-block:: http

  POST /v2/zones/1bed5d24-d487-4410-b813-f1c637db0ba3/recordsets HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {
    "name": "11.2.0.192.in-addr.arpa.",
    "description": "A PTR recordset",
    "type": "PTR",
    "ttl": 3600,
    "records": [
      "example.org."
    ]
  }

Here is the response.

.. code-block:: http

  HTTP/1.1 202 Accepted
  Location: http://127.0.0.1:9001/v2/zones/1bed5d24-d487-4410-b813-f1c637db0ba3/recordsets/a3dca24e-3eba-4523-8607-c0ad4b9a9272
  Content-Length: 499
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-5b7044d0-591a-445a-839f-1403b1455824
  Date: Fri, 20 Feb 2015 21:42:45 GMT
  Connection: keep-alive

  {
    "type": "PTR",
    "action": "CREATE",
    "version": 1,
    "created_at": "2015-02-20T21:42:45.000000",
    "zone_id": "1bed5d24-d487-4410-b813-f1c637db0ba3",
    "name": "11.2.0.192.in-addr.arpa.",
    "id": "a3dca24e-3eba-4523-8607-c0ad4b9a9272",
    "ttl": 3600,
    "records": [
      "example.org."
    ],
    "updated_at": null,
    "links": {
      "self": "http://127.0.0.1:9001/v2/zones/1bed5d24-d487-4410-b813-f1c637db0ba3/recordsets/a3dca24e-3eba-4523-8607-c0ad4b9a9272"
    },
    "description": "A PTR recordset",
    "status": "PENDING"
  }

We should now have a correct `PTR` record assigned in our nameserver
that we can test.

.. note::

   As the `in-addr.arpa.` zone is considered an admin zone, you may
   need to get admin rights in order to create the necessary
   subdomains.

Let's test it out!

.. code-block:: bash

  $ dig @localhost -x 192.0.2.11

  ; <<>> DiG 9.9.5-3ubuntu0.1-Ubuntu <<>> @localhost -x 192.0.2.11
  ; (1 server found)
  ;; global options: +cmd
  ;; Got answer:
  ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 32832
  ;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 1
  ;; WARNING: recursion requested but not available

  ;; OPT PSEUDOSECTION:
  ; EDNS: version: 0, flags:; udp: 4096
  ;; QUESTION SECTION:
  ;11.2.0.192.in-addr.arpa.    IN      PTR

  ;; ANSWER SECTION:
  11.2.0.192.in-addr.arpa. 3600 IN     PTR     example.org.

  ;; AUTHORITY SECTION:
  11.2.0.192.in-addr.arpa. 3600 IN     NS      ns1.example.org.

  ;; Query time: 3 msec
  ;; SERVER: 127.0.0.1#53(127.0.0.1)
  ;; WHEN: Fri Feb 20 21:45:53 UTC 2015
  ;; MSG SIZE  rcvd: 98

As you can see from the answer section everything worked as expected.


Advanced Usage
--------------

You can add many `PTR` records to a larger subnet by using a more
broadly defined `in-addr.arpa.` zone. For example, if we wanted to
ensure *any* IP in a subnet resolves to a specific domain.

.. code-block:: http

   POST /v2/zones HTTP/1.1
   Accept: application/json
   Content-Type: application/json

   {
     "name": "2.0.192.in-addr.arpa.",
     "ttl": 3600,
     "email": "admin@example.com"
   }

We then could use the corresponding domain to create a `PTR` record
for a specific IP.

.. code-block:: http

   POST /v2/zones/$domain_uuid/recordsets HTTP/1.1
   Accept: application/json
   Content-Type: application/json

   {
     "name": "3.2.0.192.in-addr.arpa.",
     "type": "PTR"
     "ttl": 3600,
     "records": [
       "cats.example.com."
     ]
   }

When we do our reverse look, we should see `cats.example.com.`

.. code-block:: bash

  $ dig @localhost -x 192.0.2.3 +short
  cats.example.com.

Success!

You can further specify `in-addr.arpa.` zones to chunks of IP
addresses by using Classless in-addr.arpa. Delegation. See `RFC 2317`_
for more information.

.. note::
   In BIND9, when creating a new `PTR` we could skip the zone name. For
   example, if the zone is `2.0.192.in-addr.arpa.`, using `12` for
   the record name is ends up as `12.2.0.192.in-addr.arpa.`. In
   Designate, the name of a record MUST be a complete host name.

.. _RFC 2317: https://tools.ietf.org/html/rfc2317
