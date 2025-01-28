..
    Copyright 2021 Red Hat

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


================
Managing Zones
================

In the Domain Name System, `zones` are used to break up the namespace into more
easily managed pieces. For example, within the root zone ``.`` there are zones
for each of the top level domains such as ``.org.`` and ``.com.`` and
responsiblity for each of those zones could lie with a different organisation.
Within those zones, there are then delegations to other zones, such as
``example.org.`` or ``example.com.`` which might again be managed by a
different organisation and/or set of nameservers. This forms a hierarchy of
responsibility, with the higher levels being mainly composed of delegations to
lower levels.

Zones in Designate
==================

Zones in Designate model the ownership concept from DNS itself, where any
given zone can only be owned by a single tenant. However, while DNS is able to
support a hierarchy of zones, there is no support for delegating subzones to
another tenant, and one tenant cannot create zones that lie within the zone of
another tenant.

The creation of a zone in Designate also creates two recordsets automatically:
an SOA record and an NS record. By default these records cannot be modified
without the admin role.

Zones vs Top Level Domains
---------------------------

While top level domains are considered zones from a DNS perspective, in
Designate they are often not managed as a zone, and instead have their own TLD
type that allows any tenant to create zones within that TLD and restricts
tenants from creating zones that aren't within a managed TLD. If no TLDs are
being managed within Designate, tenants can create any zone aside from the root
zone and top level domains.

Creating a zone
---------------

Creating a zone requires only the name of the zone and an email address of the
party responsible for the zone.

.. code-block:: console

   $ openstack zone create --email dnsmaster@example.com example.com.
   +----------------+--------------------------------------+
   | Field          | Value                                |
   +----------------+--------------------------------------+
   | action         | CREATE                               |
   | attributes     | {}                                   |
   | created_at     | 2016-07-13T14:54:16.000000           |
   | description    | None                                 |
   | email          | dnsmaster@example.com                |
   | id             | 14093115-0f0f-497a-ac69-42235e46c26f |
   | masters        |                                      |
   | name           | example.com.                         |
   | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
   | project_id     | 656bc359067844fba6005d400f19df76     |
   | serial         | 1468421656                           |
   | status         | PENDING                              |
   | transferred_at | None                                 |
   | ttl            | 3600                                 |
   | type           | PRIMARY                              |
   | updated_at     | None                                 |
   | version        | 1                                    |
   +----------------+--------------------------------------+

Note that the state is PENDING. Designate has received the request to create
the zone, but may not have completed it yet. After a short time, verify
successful creation of the DNS Zone:

.. code-block:: console

   $ openstack zone list
   +--------------------------------------+--------------+---------+------------+--------+--------+
   | id                                   | name         | type    |     serial | status | action |
   +--------------------------------------+--------------+---------+------------+--------+--------+
   | 14093115-0f0f-497a-ac69-42235e46c26f | example.com. | PRIMARY | 1468421656 | ACTIVE | NONE   |
   +--------------------------------------+--------------+---------+------------+--------+--------+

There will now be two recordsets visible in the zone:

.. code-block:: console

   $ openstack recordset list example.com.
   +--------------------------------------+--------------+------+---------------------------------------------------------------------+--------+--------+
   | id                                   | name         | type | records                                                             | status | action |
   +--------------------------------------+--------------+------+---------------------------------------------------------------------+--------+--------+
   | 269cf8d2-c498-49a8-aef9-01e81d078313 | example.com. | SOA  | ns1.devstack.org. admin.example.com. 1618291836 3509 600 86400 3600 | ACTIVE | NONE   |
   | 31b50023-88b2-4011-b31b-474fa25a8e39 | example.com. | NS   | ns1.devstack.org.                                                   | ACTIVE | NONE   |
   +--------------------------------------+--------------+------+---------------------------------------------------------------------+--------+--------+

The values for refresh, retry, minimum and expire on the SOA record are set by
the Designate operator. The TTL, however, can be modified by users via the
zone:

.. code-block:: console

   $ openstack zone set example.com. --ttl 3000
   +----------------+--------------------------------------+
   | Field          | Value                                |
   +----------------+--------------------------------------+
   | action         | UPDATE                               |
   | attributes     |                                      |
   | created_at     | 2021-04-13T05:30:36.000000           |
   | description    | None                                 |
   | email          | admin@example.com                    |
   | id             | b9861a55-0e50-4896-8ab9-25d8c4494f64 |
   | masters        |                                      |
   | name           | example.com.                         |
   | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
   | project_id     | 9d69e3a004aa40c581f00d7bb7763e0a     |
   | serial         | 1618545015                           |
   | status         | PENDING                              |
   | transferred_at | None                                 |
   | ttl            | 3000                                 |
   | type           | PRIMARY                              |
   | updated_at     | 2021-04-16T03:50:15.000000           |
   | version        | 11                                   |
   +----------------+--------------------------------------+

The ``dig`` tool can be used to query one of the backend nameservers to confirm
the result. In this example, there is a DNS server at ``192.168.122.186``
managed by designate as part of the default pool.

.. code-block:: console

   $ dig @192.168.122.186 example.com.

   ; <<>> DiG 9.11.20-RedHat-9.11.20-5.el8_3.1 <<>> @192.168.122.186 example.com.
   ; (1 server found)
   ;; global options: +cmd
   ;; Got answer:
   ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 63663
   ;; flags: qr aa rd; QUERY: 1, ANSWER: 0, AUTHORITY: 1, ADDITIONAL: 1
   ;; WARNING: recursion requested but not available

   ;; OPT PSEUDOSECTION:
   ; EDNS: version: 0, flags:; udp: 4096
   ; COOKIE: 970f584e4cb93505eaf46f526079097ac959da76062f1d0a (good)
   ;; QUESTION SECTION:
   ;example.com.			IN	A

   ;; AUTHORITY SECTION:
   example.com.		3000	IN	SOA	ns1.devstack.org. admin.example.com. 1618545015 3509 600 86400 3600

   ;; Query time: 0 msec
   ;; SERVER: 192.168.122.186#53(192.168.122.186)
   ;; WHEN: Fri Apr 16 03:50:18 UTC 2021
   ;; MSG SIZE  rcvd: 126

In the ``AUTHORITY`` section, the numeric value between the name and `IN` is
the TTL, which has updated to the new value of 3000.

Deleting a zone
---------------

A zone can be deleted using either its name or ID:

.. code-block:: console

   $ openstack zone delete example.com.
   +----------------+--------------------------------------+
   | Field          | Value                                |
   +----------------+--------------------------------------+
   | action         | DELETE                               |
   | attributes     |                                      |
   | created_at     | 2021-04-13T05:30:36.000000           |
   | description    | None                                 |
   | email          | admin@example.com                    |
   | id             | b9861a55-0e50-4896-8ab9-25d8c4494f64 |
   | masters        |                                      |
   | name           | example.com.                         |
   | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
   | project_id     | 9d69e3a004aa40c581f00d7bb7763e0a     |
   | serial         | 1618545024                           |
   | status         | PENDING                              |
   | transferred_at | None                                 |
   | ttl            | 3000                                 |
   | type           | PRIMARY                              |
   | updated_at     | 2021-04-16T10:18:05.000000           |
   | version        | 15                                   |
   +----------------+--------------------------------------+

Any records present in the zone are also deleted and will no longer resolve.

.. note::

   Zones that have shares cannot be deleted without removing the shares or
   using the `delete-shares` modifier.

Associating a Zone with a Pool
------------------------------
When your administrator has configured designate to use multiple DNS server
pools, it might be necessary for you to indicate a specific pool attribute or
ID when you create a zone. Your administrator will provide you with the
necessary pool information to create a zone.

In this example, the pool attribute that indicates one of several service
tiers, must be specified when creating a zone:

.. code-block:: console

   $ openstack zone create --email dnsmaster@example.com example.com. --attributes service_tier:silver
    +----------------+--------------------------------------+
    | Field          | Value                                |
    +----------------+--------------------------------------+
    | action         | CREATE                               |
    | attributes     | service_tier:silver                  |
    |                |                                      |
    | created_at     | 2023-04-04T18:30:45.000000           |
    | description    | None                                 |
    | email          | dnsmaster@example.com                |
    | id             | d106e7b0-9973-41a1-b3db-0fb34b6d952c |
    | masters        |                                      |
    | name           | example.com.                         |
    | pool_id        | 10cec123-43f0-4b60-98a8-1204dd826c67 |
    | project_id     | 5160768b59524fd283a4fa82d7327644     |
    | serial         | 1674585045                           |
    | status         | PENDING                              |
    | transferred_at | None                                 |
    | ttl            | 3600                                 |
    | type           | PRIMARY                              |
    | updated_at     | None                                 |
    | version        | 1                                    |
    +----------------+--------------------------------------+

.. note::
   Remember that

   [service:central]
   scheduler_filters = attribute

   configuration setting is required to associate a newly created zone with an existing pool.

In this example, a specific pool ID, ``7a2cde6b-d321-fa11-f99e-ccc378fe3dd1``,
must be specified when creating a zone:

.. code-block:: console

   $ openstack zone create --email dnsmaster@example.com example.com. --attributes pool_id:7a2cde6b-d321-fa11-f99e-ccc378fe3dd1
    +----------------+----------------------------------------------+
    | Field          | Value                                        |
    +----------------+----------------------------------------------+
    | action         | CREATE                                       |
    | attributes     | pool_id:7a2cde6b-d321-fa11-f99e-ccc378fe3dd1 |
    |                |                                              |
    | created_at     | 2023-04-04T18:39:12.000000                   |
    | description    | None                                         |
    | email          | dnsmaster@example.com                        |
    | id             | 54f2bcaa-65ef-8274-5fde-987234508afe         |
    | masters        |                                              |
    | name           | example.com.                                 |
    | pool_id        | 7a2cde6b-d321-fa11-f99e-ccc378fe3dd1         |
    | project_id     | 5160768b59524fd283a4fa82d7327644             |
    | serial         | 2385822109                                   |
    | status         | PENDING                                      |
    | transferred_at | None                                         |
    | ttl            | 3600                                         |
    | type           | PRIMARY                                      |
    | updated_at     | None                                         |
    | version        | 1                                            |
    +----------------+----------------------------------------------+

.. note::
   Remember that

   [service:central]
   scheduler_filters = pool_id_attribute

   configuration setting is required to associate a newly created zone with an existing pool.

Verify that the zone has been created:

.. code-block:: console

    $ openstack zone list
    +--------------------------------------+---------------+---------+------------+--------+--------+
    | id                                   | name          | type    |     serial | status | action |
    +--------------------------------------+---------------+---------+------------+--------+--------+
    | 54f2bcaa-65ef-8274-5fde-987234508afe | example.com.  | PRIMARY | 2385822109 | ACTIVE | NONE   |
    +--------------------------------------+---------------+---------+------------+--------+--------+
