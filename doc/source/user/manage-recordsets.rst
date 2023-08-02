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


====================
 Managing Records
====================

While zones are used to break up the DNS namespace into a hierarchy,
'resource records', or simply 'records', are used to store data within the
namespace. Each record has a

- **Name:** the string that indicates its location in the DNS namespace.
- **Type:** the set of `letter codes`_ that identify the record's usage. For
  example ``A`` for an address record or ``CNAME`` for a canonical name record.
- **Class:** the set of letter codes that specify the namespace for the
  record. Typically, this is ``IN`` for internet, though other namespaces do
  exist.
- **TTL:** the duration in seconds that the record remains valid.
- **Rdata:** the data for the record, such as an IP address for an ``A`` type
  record or another record name for a ``CNAME`` type record.

Recordsets in Designate
=======================

DNS records in Designate are managed using ``Recordsets``, which represent one
or more DNS records with the same `Name` and `Type`, but potentially different
data. For example, a recordset named ``www.example.com``, with a type of ``A``,
that contains the data ``192.0.2.1`` and ``192.0.2.2`` might reflect two web
servers hosting ``www.example.com`` located at those two IP addresses.

You must create Recordsets within a zone. If you delete a zone that contains
recordsets, those recordsets within the zone are also deleted.

Creating a recordset
--------------------

By default, any user can create Recordsets in zones that their project owns.
In this example, a user has created a zone named ``example.org.``.

Recordsets are created using the ``openstack recordset create`` command and
require a zone, a name, a type, and data for the record.
To recreate the earlier example using the OpenStack client with the Designate
plugin, the user would run:


.. code-block:: console

   $ openstack recordset create --type A --record 192.0.2.1 example.org. www
   +-------------+--------------------------------------+
   | Field       | Value                                |
   +-------------+--------------------------------------+
   | action      | CREATE                               |
   | created_at  | 2021-05-03T03:13:46.000000           |
   | description | None                                 |
   | id          | 549c3e83-443f-474b-b467-6bcd7cb9f37d |
   | name        | www.example.org.                     |
   | project_id  | c85fdba96041438fa0cad2dc7909d3f5     |
   | records     | 192.0.2.1                            |
   | status      | PENDING                              |
   | ttl         | None                                 |
   | type        | A                                    |
   | updated_at  | None                                 |
   | version     | 1                                    |
   | zone_id     | 077460ef-34db-486a-8d59-c9564dc3a3a9 |
   | zone_name   | example.org.                         |
   +-------------+--------------------------------------+

As the final argument ``www`` is not a fully qualified domain name (FQDN) it
is prepended to the zone name. You can achieve the same result using the FQDN,
``www.example.org.``. Note that the trailing ``.`` is required when using the
FQDN. Omitting it results in the name, ``"www.example.org.example.org."``.

You can supply the ``--record`` argument  multiple times to create multiple
records within the recordset. A typical use for this is `Round-robin DNS`_.


.. code-block:: console

   $ openstack recordset create --type A --record 192.0.2.1 --record 192.0.2.2 example.org. web
   +-------------+--------------------------------------+
   | Field       | Value                                |
   +-------------+--------------------------------------+
   | action      | CREATE                               |
   | created_at  | 2021-05-03T03:26:43.000000           |
   | description | None                                 |
   | id          | 9e0fba43-ca67-44ed-b9d9-fc1242920319 |
   | name        | web.example.org.                     |
   | project_id  | c85fdba96041438fa0cad2dc7909d3f5     |
   | records     | 192.0.2.1                            |
   |             | 192.0.2.2                            |
   | status      | PENDING                              |
   | ttl         | None                                 |
   | type        | A                                    |
   | updated_at  | None                                 |
   | version     | 1                                    |
   | zone_id     | 077460ef-34db-486a-8d59-c9564dc3a3a9 |
   | zone_name   | example.org.                         |
   +-------------+--------------------------------------+

You can view the recordsets for a zone using the ``openstack recordset list``
command:

.. code-block:: console

   $ openstack recordset list example.org.
   +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+
   | id                                   | name             | type | records                                                             | status | action |
   +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+
   | 3bebbd03-07d7-4274-a784-39c32a2be8c6 | example.org.     | SOA  | ns1.example.net. admin.example.org. 1620012616 3599 600 86400 3600  | ACTIVE | NONE   |
   | 7d34e4d3-a2f1-4af0-831c-ba52a8312c6a | example.org.     | NS   | ns1.example.net.                                                    | ACTIVE | NONE   |
   | 9e0fba43-ca67-44ed-b9d9-fc1242920319 | web.example.org. | A    | 192.0.2.1                                                           | ACTIVE | NONE   |
   |                                      |                  |      | 192.0.2.2                                                           |        |        |
   | 549c3e83-443f-474b-b467-6bcd7cb9f37d | www.example.org. | A    | 192.0.2.1                                                           | ACTIVE | NONE   |
   +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+

The ``SOA`` and ``NS`` records for the zone are also visible here, but cannot
be modified.

The authoritative nameserver for the zone is listed as the record data for the
``NS`` type record of the zone, which in this example is ``ns1.example.net.``.
To verify this you can query the nameserver using ``dig`` for the ``NS`` type:

.. code-block:: console

   $ dig @ns1.example.net example.org. -t NS +short
   ns1.devstack.org.

You can also verify the ``A`` recordsets. You don't need the ``-t`` option
because it is the default:

.. code-block:: console

   $ dig @ns1.example.net web.example.org. +short
   192.0.2.2
   192.0.2.1
   $ dig @ns1.example.net www.example.org. +short
   192.0.2.1

If you want to construct a ``TXT`` record that exceeds the 255-octet
maximum length of a character-string, it has to be split into
multiple strings as defined in RFC7208 section 3.3. For example,
``"v=DKIM1; .... firstsecond string..."`` can become
``"v=DKIM1; .... first" "second string..."``. If you provide a record
data with less than 255 characters, it will be treated as a
single character-string and validated for empty spaces outside quotes
and unescaped double quotation marks as in RFC1035 section 5.1.

For example, to create a ``TXT`` record made of one string of 410
characters you can split it into 2 to like this:

.. code-block:: console

   $ openstack recordset create --type TXT --record '"210 characters string" "200 characters string"' example.org. _domainkey

Updating a recordset
--------------------

You can modify a recordset by using the ``openstack recordset set`` command.
When updating a recordset by name, you must use the FQDN. As with most
OpenStack commands, you can also use recordset ID. For example, to update
the recordset ``www.example.org.`` to contain two records, you could use
the following:

.. code-block:: console

   $ openstack recordset set example.org. www.example.org. --record 192.0.2.1 --record 192.0.2.2
   +-------------+--------------------------------------+
   | Field       | Value                                |
   +-------------+--------------------------------------+
   | action      | UPDATE                               |
   | created_at  | 2021-05-03T03:30:16.000000           |
   | description | None                                 |
   | id          | 549c3e83-443f-474b-b467-6bcd7cb9f37d |
   | name        | www.example.org.                     |
   | project_id  | c85fdba96041438fa0cad2dc7909d3f5     |
   | records     | 192.0.2.2                            |
   |             | 192.0.2.1                            |
   | status      | PENDING                              |
   | ttl         | None                                 |
   | type        | A                                    |
   | updated_at  | 2021-05-03T03:44:16.000000           |
   | version     | 5                                    |
   | zone_id     | 077460ef-34db-486a-8d59-c9564dc3a3a9 |
   | zone_name   | example.org.                         |
   +-------------+--------------------------------------+

Deleting a recordset
--------------------

You can use the ``openstack recordset delete`` command to remove recordsets
using the zone and either the FQDN or the recordset ID.

.. code-block:: console

   $ openstack recordset delete example.org. web.example.org.
   +-------------+--------------------------------------+
   | Field       | Value                                |
   +-------------+--------------------------------------+
   | action      | DELETE                               |
   | created_at  | 2021-05-03T03:47:00.000000           |
   | description | None                                 |
   | id          | 5ab3418f-5377-47eb-b967-9e9ff7f3c26b |
   | name        | web.example.org.                     |
   | project_id  | c85fdba96041438fa0cad2dc7909d3f5     |
   | records     | 192.0.2.1                            |
   |             | 192.0.2.2                            |
   | status      | PENDING                              |
   | ttl         | None                                 |
   | type        | A                                    |
   | updated_at  | 2021-05-03T03:47:13.000000           |
   | version     | 2                                    |
   | zone_id     | 077460ef-34db-486a-8d59-c9564dc3a3a9 |
   | zone_name   | example.org.                         |
   +-------------+--------------------------------------+

.. _letter codes: https://en.wikipedia.org/wiki/List_of_DNS_record_types
.. _Round-robin DNS: https://en.wikipedia.org/wiki/Round-robin_DNS
