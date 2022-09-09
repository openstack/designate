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
addresses to a fully qualified domain name (FQDN). For example,

.. code-block:: console

    $ dig -x 192.0.2.12 +short
    example.org.

The way this works in the DNS system is through the `in-addr.arpa.`
zone. For example

.. code-block:: console

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

To create a `PTR` record in Designate we need a `in-addr.arpa.` zone
that will receive the actual `PTR` record


Using the V2 API and the OpenStack CLI
--------------------------------------

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
    Location: http://127.0.0.1:9001/v2/zones/251fbde4-6eb8-44e6-bc48-e095f1763a1f
    Content-Length: 476
    Content-Type: application/json; charset=UTF-8
    X-Openstack-Request-Id: req-bfcd0723-624c-4ec2-bbd5-99e985efe8db
    Date: Tue, 02 Jun 2020 17:24:10 GMT
    Connection: keep-alive

    {
      "id": "251fbde4-6eb8-44e6-bc48-e095f1763a1f",
      "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
      "project_id": "123d51544df443e790b8e95cce52c285",
      "name": "example.org.",
      "email": "admin@example.org",
      "description": "A great example zone",
      "ttl": 3600,
      "serial": 1591118650,
      "status": "PENDING",
      "action": "CREATE",
      "version": 1,
      "attributes": {},
      "type": "PRIMARY",
      "masters": [],
      "created_at": "2020-06-02T17:24:10.000000",
      "updated_at": null,
      "transferred_at": null,
      "links": {
        "self": "http://127.0.0.1:9001/v2/zones/251fbde4-6eb8-44e6-bc48-e095f1763a1f"
      }
    }

Using the CLI:

.. code-block:: console

    $ openstack zone create --email admin@example.org \
        --description "A great example zone" --ttl 3600 example.org.
    +----------------+--------------------------------------+
    | Field          | Value                                |
    +----------------+--------------------------------------+
    | action         | CREATE                               |
    | attributes     |                                      |
    | created_at     | 2020-06-02T17:24:10.000000           |
    | description    | A great example zone                 |
    | email          | admin@example.org                    |
    | id             | 251fbde4-6eb8-44e6-bc48-e095f1763a1f |
    | masters        |                                      |
    | name           | example.org.                         |
    | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
    | project_id     | 123d51544df443e790b8e95cce52c285     |
    | serial         | 1591118650                           |
    | status         | PENDING                              |
    | transferred_at | None                                 |
    | ttl            | 3600                                 |
    | type           | PRIMARY                              |
    | updated_at     | None                                 |
    | version        | 1                                    |
    +----------------+--------------------------------------+

.. note::

    The `status` is `PENDING`. If we make a `GET` request to
    the `self` field in the zone, it will most likely have been
    processed and updated to `ACTIVE`.

Now that we have a zone we would like to use for our reverse DNS
lookup, we need to add an `in-addr.arpa.` zone that includes the IP
address we want to look up.

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
      "description": "A in-addr.arpa. zone for reverse lookups"
    }

As you can see, in the `name` field we've reversed our IP address and
used that as a subdomain in the `in-addr.arpa.` zone.

Here is the response.

.. code-block:: http

    HTTP/1.1 202 Accepted
    Location: http://127.0.0.1:9001/v2/zones/f5546034-b27e-4326-bf9d-c53ed879f7fa
    Content-Length: 512
    Content-Type: application/json; charset=UTF-8
    X-Openstack-Request-Id: req-4e691123-045e-4f8e-ae50-b5eabb5af3fa
    Date: Tue, 02 Jun 2020 17:32:46
    Connection: keep-alive

    {
      "id": "f5546034-b27e-4326-bf9d-c53ed879f7fa",
      "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
      "project_id": "123d51544df443e790b8e95cce52c285",
      "name": "11.2.0.192.in-addr.arpa.",
      "email": "admin@example.org",
      "description": "A in-addr.arpa. zone for reverse lookups",
      "ttl": 3600,
      "serial": 1591119166,
      "status": "PENDING",
      "action": "CREATE",
      "version": 1,
      "attributes": {},
      "type": "PRIMARY",
      "masters": [],
      "created_at": "2020-06-02T17:32:47.000000",
      "updated_at": null,
      "transferred_at": null,
      "links": {
        "self": "http://127.0.0.1:9001/v2/zones/f5546034-b27e-4326-bf9d-c53ed879f7fa"
      }
    }

Using the CLI:

.. code-block:: console

    $ openstack zone create --email admin@example.org \
        --ttl 3600 --description "A in-addr.arpa. zone for reverse lookups" \
        11.2.0.192.in-addr.arpa.
    +----------------+------------------------------------------+
    | Field          | Value                                    |
    +----------------+------------------------------------------+
    | action         | CREATE                                   |
    | attributes     |                                          |
    | created_at     | 2020-06-02T17:32:47.000000               |
    | description    | A in-addr.arpa. zone for reverse lookups |
    | email          | admin@example.org                        |
    | id             | f5546034-b27e-4326-bf9d-c53ed879f7fa     |
    | masters        |                                          |
    | name           | 11.2.0.192.in-addr.arpa.                 |
    | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842     |
    | project_id     | 123d51544df443e790b8e95cce52c285         |
    | serial         | 1591119166                               |
    | status         | PENDING                                  |
    | transferred_at | None                                     |
    | ttl            | 3600                                     |
    | type           | PRIMARY                                  |
    | updated_at     | None                                     |
    | version        | 1                                        |
    +----------------+------------------------------------------+

Now that we have our `in-addr.arpa.` zone, we add a new `PTR` record
to the zone.

.. code-block:: http

    POST /v2/zones/f5546034-b27e-4326-bf9d-c53ed879f7fa/recordsets HTTP/1.1
    Content-Type: application/json
    Accept: application/json

    {
      "name": "11.2.0.192.in-addr.arpa.",
      "type": "PTR",
      "records": [
        "example.org."
      ],
      "ttl": 3600,
      "description": "A PTR recordset"
    }

Here is the response.

.. code-block:: http

    HTTP/1.1 202 Accepted
    Location: http://127.0.0.1:9001/v2/zones/f5546034-b27e-4326-bf9d-c53ed879f7fa/recordsets/ca604f72-83e6-421f-bf1c-bb4dc1df994a
    Content-Length: 573
    Content-Type: application/json; charset=UTF-8
    X-Openstack-Request-Id: req-5b7044d0-591a-445a-839f-1403b1455824
    Date: Tue, 02 Jun 2020 19:55:50 GMT
    Connection: keep-alive

    {
      "id": "ca604f72-83e6-421f-bf1c-bb4dc1df994a",
      "zone_id": "f5546034-b27e-4326-bf9d-c53ed879f7fa",
      "project_id": "123d51544df443e790b8e95cce52c285",
      "name": "11.2.0.192.in-addr.arpa.",
      "zone_name": "11.2.0.192.in-addr.arpa.",
      "type": "PTR",
      "records": [
        "example.org."
      ],
      "description": "A PTR recordset",
      "ttl": 3600,
      "status": "PENDING",
      "action": "CREATE",
      "version": 1,
      "created_at": "2020-06-02T19:55:50.000000",
      "updated_at": null,
      "links": {
        "self": "http://127.0.0.1:9001/v2/zones/f5546034-b27e-4326-bf9d-c53ed879f7fa/recordsets/ca604f72-83e6-421f-bf1c-bb4dc1df994a"
      }
    }

With the CLI:

.. code-block:: console

    $ openstack recordset create --record example.org. --type PTR \
        --ttl 3600 --description "A PTR recordset" \
        11.2.0.192.in-addr.arpa. 11.2.0.192.in-addr.arpa.
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | action      | CREATE                               |
    | created_at  | 2020-06-02T19:55:50.000000           |
    | description | A PTR recordset                      |
    | id          | ca604f72-83e6-421f-bf1c-bb4dc1df994a |
    | name        | 11.2.0.192.in-addr.arpa.             |
    | project_id  | 123d51544df443e790b8e95cce52c285     |
    | records     | example.org.                         |
    | status      | PENDING                              |
    | ttl         | 3600                                 |
    | type        | PTR                                  |
    | updated_at  | None                                 |
    | version     | 1                                    |
    | zone_id     | f5546034-b27e-4326-bf9d-c53ed879f7fa |
    | zone_name   | 11.2.0.192.in-addr.arpa.             |
    +-------------+--------------------------------------+

We should now have a correct `PTR` record assigned in our nameserver
that we can test.

Let's test it out!

.. code-block:: console

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

IPv6
----

Following the previous example we will configure `fd00::2:11` to
return our `example.org.` domain name. As reverse DNS lookups for
`IPv6` addresses use the special domain `ip6.arpa`, we need to create

.. code-block:: console

    $ openstack zone create --email admin@example.org \
        --ttl 3600 --description "A ip6.arpa zone for IPv6 reverse lookups" \
        1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa.
    +----------------+---------------------------------------------------------------------------+
    | Field          | Value                                                                     |
    +----------------+---------------------------------------------------------------------------+
    | action         | CREATE                                                                    |
    | attributes     |                                                                           |
    | created_at     | 2020-06-04T13:07:36.000000                                                |
    | description    | IPv6 reverse lookup zone                                                  |
    | email          | admin@example.org                                                         |
    | id             | 9c8f30a1-6d9d-4f40-9fac-ab8abfb24fba                                      |
    | masters        |                                                                           |
    | name           | 1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa. |
    | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842                                      |
    | project_id     | 123d51544df443e790b8e95cce52c285                                          |
    | serial         | 1591276055                                                                |
    | status         | PENDING                                                                   |
    | transferred_at | None                                                                      |
    | ttl            | 3600                                                                      |
    | type           | PRIMARY                                                                   |
    | updated_at     | None                                                                      |
    | version        | 1                                                                         |
    +----------------+---------------------------------------------------------------------------+

And add the `PTR` record

.. code-block:: console

    $ openstack recordset create --record example.org. --type PTR \
        --ttl 3600 --description "A PTR recordset" \
        1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa. \
        1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa.
    +-------------+---------------------------------------------------------------------------+
    | Field       | Value                                                                     |
    +-------------+---------------------------------------------------------------------------+
    | action      | CREATE                                                                    |
    | created_at  | 2020-06-04T13:10:30.000000                                                |
    | description | A PTR recordset                                                           |
    | id          | 246c5cbb-315d-437d-a52f-bf0a0cfa91a0                                      |
    | name        | 1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa. |
    | project_id  | 123d51544df443e790b8e95cce52c285                                          |
    | records     | example.org.                                                              |
    | status      | PENDING                                                                   |
    | ttl         | 3600                                                                      |
    | type        | PTR                                                                       |
    | updated_at  | None                                                                      |
    | version     | 1                                                                         |
    | zone_id     | 9c8f30a1-6d9d-4f40-9fac-ab8abfb24fba                                      |
    | zone_name   | 1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa. |
    +-------------+---------------------------------------------------------------------------+

Now we can do a reverse lookup with

.. code-block:: console

    $ dig @localhost -x fd00::2:11

    ; <<>> DiG 9.11.3-1ubuntu1.12-Ubuntu <<>> @10.5.0.32 -x fd00::2:11
    ; (1 server found)
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 50892
    ;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 1, ADDITIONAL: 1

    ;; OPT PSEUDOSECTION:
    ; EDNS: version: 0, flags:; udp: 4096
    ; COOKIE: 812dd247d36b98504b6d12485ed8f44bd7ae0a902343c348 (good)
    ;; QUESTION SECTION:
    ;1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa. IN PTR

    ;; ANSWER SECTION:
    1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa. 3600 IN PTR example.org.

    ;; AUTHORITY SECTION:
    1.1.0.0.2.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.f.ip6.arpa. 3600 IN NS ns1.example.org.

    ;; Query time: 1 msec
    ;; SERVER: 127.0.0.1#53(127.0.0.1)
    ;; WHEN: Thu Jun 04 13:16:59 UTC 2020
    ;; MSG SIZE  rcvd: 197

Advanced Usage
--------------

You can add many `PTR` records to a larger subnet by using a more
broadly defined `in-addr.arpa.` zone. For example, if we wanted to
ensure *any* IP in a subnet resolves to a specific domain we would add
a wildcard DNS record to this zone.

.. code-block:: http

    POST /v2/zones HTTP/1.1
    Accept: application/json
    Content-Type: application/json

    {
      "name": "2.0.192.in-addr.arpa.",
      "type": "PRIMARY",
      "email": "admin@example.org",
      "ttl": 3600,
      "description": "A more broadly defined in-addr.arpa. zone for reverse lookups"
    }

With the CLI:

.. code-block:: console

    $ openstack zone create --email admin@example.org --ttl 3600 \
        --description "A more broadly defined in-addr.arpa. zone for reverse lookups" \
        2.0.192.in-addr.arpa.
    +----------------+---------------------------------------------------------------+
    | Field          | Value                                                         |
    +----------------+---------------------------------------------------------------+
    | action         | CREATE                                                        |
    | attributes     |                                                               |
    | created_at     | 2020-06-02T20:07:11.000000                                    |
    | description    | A more broadly defined in-addr.arpa. zone for reverse lookups |
    | email          | admin@example.org                                             |
    | id             | e9fd0ced-1d3e-43fa-b9aa-6d4b7a73988d                          |
    | masters        |                                                               |
    | name           | 2.0.192.in-addr.arpa.                                         |
    | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842                          |
    | project_id     | 123d51544df443e790b8e95cce52c285                              |
    | serial         | 1591128431                                                    |
    | status         | PENDING                                                       |
    | transferred_at | None                                                          |
    | ttl            | 3600                                                          |
    | type           | PRIMARY                                                       |
    | updated_at     | None                                                          |
    | version        | 1                                                             |
    +----------------+---------------------------------------------------------------+

We then could use the corresponding domain to create a `PTR` record
for a specific IP.

.. code-block:: http

    POST /v2/zones/e9fd0ced-1d3e-43fa-b9aa-6d4b7a73988d/recordsets HTTP/1.1
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

With the CLI:

.. code-block:: console

    $ openstack recordset create --record cats.example.org. --type PTR \
        --ttl 3600 2.0.192.in-addr.arpa. 3.2.0.192.in-addr.arpa.
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | action      | CREATE                               |
    | created_at  | 2020-06-02T20:10:54.000000           |
    | description | None                                 |
    | id          | c843729b-7aaf-4f99-a40a-d9bf70edf271 |
    | name        | 3.2.0.192.in-addr.arpa.              |
    | project_id  | 123d51544df443e790b8e95cce52c285     |
    | records     | cats.example.org.                    |
    | status      | PENDING                              |
    | ttl         | 3600                                 |
    | type        | PTR                                  |
    | updated_at  | None                                 |
    | version     | 1                                    |
    | zone_id     | e9fd0ced-1d3e-43fa-b9aa-6d4b7a73988d |
    | zone_name   | 2.0.192.in-addr.arpa.                |
    +-------------+--------------------------------------+

Or with a wildcard DNS record:

.. code-block:: console

    $ openstack recordset create --record example.org. --type PTR \
        --ttl 3600 2.0.192.in-addr.arpa. *.2.0.192.in-addr.arpa.
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | action      | CREATE                               |
    | created_at  | 2020-06-04T12:22:45.000000           |
    | description | None                                 |
    | id          | 4fa96619-a1f8-4409-ba5f-fa904db4c97c |
    | name        | *.2.0.192.in-addr.arpa.              |
    | project_id  | 123d51544df443e790b8e95cce52c285     |
    | records     | example.org.                         |
    | status      | PENDING                              |
    | ttl         | 3600                                 |
    | type        | PTR                                  |
    | updated_at  | None                                 |
    | version     | 1                                    |
    | zone_id     | e9fd0ced-1d3e-43fa-b9aa-6d4b7a73988d |
    | zone_name   | 2.0.192.in-addr.arpa.                |
    +-------------+--------------------------------------+

When we do our reverse look, we should see `cats.example.com.`

.. code-block:: console

    $ dig @localhost -x 192.0.2.3 +short
    cats.example.com.

When we query any other IP address in `192.0.2.0/24` we get

.. code-block:: console

    $ dig @10.5.0.32 -x 192.0.2.10 +short
    example.org.

Success!

.. note::

    In BIND9, when creating a new `PTR` we could skip the zone name.
    For example, if the zone is `2.0.192.in-addr.arpa.`, using `12`
    for the record name ends up as `12.2.0.192.in-addr.arpa.`. In
    Designate, the name of a record MUST be a complete host name.

Classless IN-Addr.ARPA Delegation
=================================

You may want to delegate blocks of IP addresses to projects that do not align
to subnet boundries. For example, if you wanted to give project "A" three IP
addresses. To allow project "A" to manage DNS records for those three
addresses, without delegating a whole subnet zone to project "A", you can use
classless IN-ADDR.ARPA delegation as described in `RFC 2317`_.

.. note::

    As discussed in section 4 of `RFC 2317`_, the examples in the RFC use
    '/' in the delegated zones but '-' is recommended.
    Designate will not allow you to use '/' in zone names. You will need
    to use the recommended '-' instead.

.. _RFC 2317: https://tools.ietf.org/html/rfc2317

In this example, we will delegate a PTR zone for three IP addresses, from the
192.0.2.0/24 subnet, to the `Demo` project '9284a20339184a9bb299386c380211c7'.

.. note::

    Unless noted in the examples, the commands are using a credential with
    an admin role. This is not necessary, but is a typical use case.

First, the full subnet in-addr.arpa zone will need to be created:

.. code-block:: console

    $ openstack zone create --email me@example.com 2.0.192.in-addr.arpa.
    +----------------+--------------------------------------+
    | Field          | Value                                |
    +----------------+--------------------------------------+
    | action         | CREATE                               |
    | attributes     |                                      |
    | created_at     | 2022-09-09T20:05:41.000000           |
    | description    | None                                 |
    | email          | me@example.com                       |
    | id             | bbdf0e8f-8d73-4659-ae62-f59e95a31cd7 |
    | masters        |                                      |
    | name           | 2.0.192.in-addr.arpa.                |
    | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
    | project_id     | cc5ab848dbe7462e9c7603d54a9af90f     |
    | serial         | 1662753940                           |
    | status         | PENDING                              |
    | transferred_at | None                                 |
    | ttl            | 3600                                 |
    | type           | PRIMARY                              |
    | updated_at     | None                                 |
    | version        | 1                                    |
    +----------------+--------------------------------------+

Next we will create the delegated zone:

.. code-block:: console

    $ openstack zone create --email me@example.com 1-3.2.0.192.in-addr.arpa.
    +----------------+--------------------------------------+
    | Field          | Value                                |
    +----------------+--------------------------------------+
    | action         | CREATE                               |
    | attributes     |                                      |
    | created_at     | 2022-09-09T20:06:59.000000           |
    | description    | None                                 |
    | email          | me@example.com                       |
    | id             | 2d353ed7-cb7f-4ff7-9c1e-54481304f4cb |
    | masters        |                                      |
    | name           | 1-3.2.0.192.in-addr.arpa.            |
    | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
    | project_id     | cc5ab848dbe7462e9c7603d54a9af90f     |
    | serial         | 1662754018                           |
    | status         | PENDING                              |
    | transferred_at | None                                 |
    | ttl            | 3600                                 |
    | type           | PRIMARY                              |
    | updated_at     | None                                 |
    | version        | 1                                    |
    +----------------+--------------------------------------+

Now we can share the delegated zone with the `Demo` project:

.. code-block:: console

    $ openstack zone share create 1-3.2.0.192.in-addr.arpa. 9284a20339184a9bb299386c380211c7
    +-------------------+--------------------------------------+
    | Field             | Value                                |
    +-------------------+--------------------------------------+
    | created_at        | 2022-09-09T20:07:20.000000           |
    | id                | 7859ca43-bcee-4fd1-aa2d-efda17b75198 |
    | project_id        | cc5ab848dbe7462e9c7603d54a9af90f     |
    | target_project_id | 9284a20339184a9bb299386c380211c7     |
    | updated_at        | None                                 |
    | zone_id           | 2d353ed7-cb7f-4ff7-9c1e-54481304f4cb |
    +-------------------+--------------------------------------+

Once we have the zones created and shared, we can now add the CNAME records to
the full subnet zone that point to the delegated zone records. This will need
to be repeated for each IP address being delegated. This example creates the
first CNAME record for the 192.0.2.1 IP address.

.. code-block:: console

    $ openstack recordset create --record 1.1-3.2.0.192.in-addr.arpa. --type CNAME 2.0.192.in-addr.arpa. 1.2.0.192.in-addr.arpa.
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | action      | CREATE                               |
    | created_at  | 2022-09-09T20:09:16.000000           |
    | description | None                                 |
    | id          | 482bd367-9815-4d86-a93d-734bbc92499a |
    | name        | 1.2.0.192.in-addr.arpa.              |
    | project_id  | cc5ab848dbe7462e9c7603d54a9af90f     |
    | records     | 1.1-3.2.0.192.in-addr.arpa.          |
    | status      | PENDING                              |
    | ttl         | None                                 |
    | type        | CNAME                                |
    | updated_at  | None                                 |
    | version     | 1                                    |
    | zone_id     | bbdf0e8f-8d73-4659-ae62-f59e95a31cd7 |
    | zone_name   | 2.0.192.in-addr.arpa.                |
    +-------------+--------------------------------------+

Finally, members of the `Demo` project can now create the PTR records for the
delegates IP addresses. In this example the administrator will create the first
record on behalf of the `Demo` project.

.. code-block:: console

    $ openstack recordset create --sudo-project-id 9284a20339184a9bb299386c380211c7 --record www.example.com. --type PTR 1-3.2.0.192.in-addr.arpa. 1.1-3.2.0.192.in-addr.arpa.
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | action      | CREATE                               |
    | created_at  | 2022-09-09T20:08:17.000000           |
    | description | None                                 |
    | id          | cea3f3ce-687b-422c-a378-bdcfe382a159 |
    | name        | 1.1-3.2.0.192.in-addr.arpa.          |
    | project_id  | 9284a20339184a9bb299386c380211c7     |
    | records     | www.example.com.                     |
    | status      | PENDING                              |
    | ttl         | None                                 |
    | type        | PTR                                  |
    | updated_at  | None                                 |
    | version     | 1                                    |
    | zone_id     | 2d353ed7-cb7f-4ff7-9c1e-54481304f4cb |
    | zone_name   | 1-3.2.0.192.in-addr.arpa.            |
    +-------------+--------------------------------------+

We can now use dig to query a recursive resolver to verify the delegation:

.. code-block:: console

    $ dig -x 192.0.2.1 @198.51.100.5

    ; <<>> DiG 9.16.32-RH <<>> -x 192.0.2.1 @198.51.100.5
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 16209
    ;; flags: qr aa rd ra; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

    ;; OPT PSEUDOSECTION:
    ; EDNS: version: 0, flags:; udp: 4096
    ; COOKIE: a415d9b43dcef11c01000000631ba068973cbfbf5b765032 (good)
    ;; QUESTION SECTION:
    ;1.2.0.192.in-addr.arpa.		IN	PTR

    ;; ANSWER SECTION:
    1.2.0.192.in-addr.arpa.	3600	IN	CNAME	1.1-3.2.0.192.in-addr.arpa.
    1.1-3.2.0.192.in-addr.arpa. 3600 IN	PTR	www.example.com.

    ;; Query time: 0 msec
    ;; SERVER: 198.51.100.5#53(198.51.100.5)
    ;; WHEN: Fri Sep 09 13:22:00 PDT 2022
    ;; MSG SIZE  rcvd: 149

.. note::

    Your resolver or DNS server settings (such as allow recursion and/or
    minimal responses) may cause dig to only display the CNAME and not resolve
    the PTR record in the same request.
