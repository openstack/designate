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

.. _importexport:

======================
Zone Import and Export
======================

Overview
========

Zones can be imported into and serialised out of Designate using the zone
import and export APIs. Using the `zone file format`_ along with these APIs
you can both create zones and recordsets in batches and export zone data
from Designate easily.

Exporting Zones
===============

You can export a zone file from Designate using the `zone export create`
subcommand on an existing zone, and subsequently access the exported
zone file using `zone export showfile`.

For example, use `openstack recordset list` to view the records for
a zone you'd like to export:

.. code-block:: console

  $ openstack recordset list example.org.
  +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+
  | id                                   | name             | type | records                                                             | status | action |
  +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+
  | b4dfeb36-c4ae-4399-9493-6e6997099356 | example.org.     | NS   | ns1.example.org.                                                    | ACTIVE | NONE   |
  | e9e3b31f-8aef-465f-9380-e3380191f8bd | example.org.     | SOA  | ns1.example.org. admin.example.org. 1624414033 3583 600 86400 3600  | ACTIVE | NONE   |
  | 09407eaa-1fac-4257-b9e1-11d693bc1eae | www.example.org. | A    | 192.0.2.2                                                           | ACTIVE | NONE   |
  |                                      |                  |      | 192.0.2.1                                                           |        |        |
  +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+

Using the `openstack zone export create` command, export `example.org.`:

.. code-block:: console

  $ openstack zone export create example.org.
  +------------+--------------------------------------+
  | Field      | Value                                |
  +------------+--------------------------------------+
  | created_at | 2021-06-23T02:01:30.000000           |
  | id         | e75aef2c-b562-4cd9-a426-4a73f6cb82be |
  | location   | None                                 |
  | message    | None                                 |
  | project_id | cf5a8f5cc5834d2dacd1d54cd0a354b7     |
  | status     | PENDING                              |
  | updated_at | None                                 |
  | version    | 1                                    |
  | zone_id    | d8f81db6-937b-4388-bfb3-ba620e6c09fb |
  +------------+--------------------------------------+

You can access the contents of the zone file using `zone export showfile`.
Using the `-f value` parameter will print the contents of the zone file without
any tabulation, which can be useful if you want to modify the exported zone
file locally and then import it back into Designate to update the zone.

.. code-block:: console

  $ openstack zone export showfile e75aef2c-b562-4cd9-a426-4a73f6cb82be -f value
  $ORIGIN example.org.
  $TTL 3600

  example.org.  IN NS ns1.example.org.
  example.org.  IN SOA ns1.example.org. admin.example.org. 1624414033 3583 600 86400 3600

  www.example.org.  IN A 192.0.2.2
  www.example.org.  IN A 192.0.2.1

By default, the zone export file will be created on demand as it is accessed
and as a result the contents of the zone export file will be updated as you
add new recordsets to the zone:

.. code-block:: console

  $ openstack recordset create example.org. test --type A --record 192.0.2.100
  +-------------+--------------------------------------+
  | Field       | Value                                |
  +-------------+--------------------------------------+
  | action      | CREATE                               |
  | created_at  | 2021-06-23T02:35:06.000000           |
  | description | None                                 |
  | id          | aa27ccd8-77b1-41df-a3ed-2129259b334a |
  | name        | test.example.org.                    |
  | project_id  | cf5a8f5cc5834d2dacd1d54cd0a354b7     |
  | records     | 192.0.2.100                          |
  | status      | PENDING                              |
  | ttl         | None                                 |
  | type        | A                                    |
  | updated_at  | None                                 |
  | version     | 1                                    |
  | zone_id     | d8f81db6-937b-4388-bfb3-ba620e6c09fb |
  | zone_name   | example.org.                         |
  +-------------+--------------------------------------+
  $ openstack zone export showfile e75aef2c-b562-4cd9-a426-4a73f6cb82be -f value
  $ORIGIN example.org.
  $TTL 3600

  example.org.  IN NS ns1.example.org.
  example.org.  IN SOA ns1.example.org. admin.example.org. 1624415706 3583 600 86400 3600
  www.example.org.  IN A 192.0.2.2
  www.example.org.  IN A 192.0.2.1
  test.example.org.  IN A 192.0.2.100

Zone Export Internals
---------------------

The zone export resource created does not contain the zone file data, instead
it holds the location of that data as Designate can be configured by the
operator to store zone exports in external services. By default, the location
of the zone export file is internal to Designate and uses the Designate
protocol `designate://`. In this case, zone file data will be generated on
demand when `zone export showfile` is used. You can view the location URI of
the zone file data using `zone export show`:

.. code-block:: console

  $ openstack zone export show e75aef2c-b562-4cd9-a426-4a73f6cb82be
  +------------+--------------------------------------------------------------------------------+
  | Field      | Value                                                                          |
  +------------+--------------------------------------------------------------------------------+
  | created_at | 2021-06-23T02:01:30.000000                                                     |
  | id         | e75aef2c-b562-4cd9-a426-4a73f6cb82be                                           |
  | location   | designate://v2/zones/tasks/exports/e75aef2c-b562-4cd9-a426-4a73f6cb82be/export |
  | message    | None                                                                           |
  | project_id | cf5a8f5cc5834d2dacd1d54cd0a354b7                                               |
  | status     | COMPLETE                                                                       |
  | updated_at | 2021-06-23T02:01:30.000000                                                     |
  | version    | 2                                                                              |
  | zone_id    | d8f81db6-937b-4388-bfb3-ba620e6c09fb                                           |
  +------------+--------------------------------------------------------------------------------+

Zone Import
===========

You can import a zone and all of its recordsets by putting them all into a
file that uses the `zone file format`_ and calling
`openstack zone import create`:

.. code-block:: console

  $ cat zone_file
  $ORIGIN example.org.
  $TTL 3600

  example.org.  IN NS ns1.example.org.
  example.org.  IN SOA ns1.example.org. admin.example.org. 1624415706 3583 600 86400 3600
  www.example.org.  IN A 192.0.2.2
  www.example.org.  IN A 192.0.2.1
  test.example.org.  IN A 192.0.2.100

  $ openstack zone import create zone_file
  +------------+--------------------------------------+
  | Field      | Value                                |
  +------------+--------------------------------------+
  | created_at | 2021-06-24T03:39:58.000000           |
  | id         | 6140580d-c72a-4f07-82ab-908da979a9a3 |
  | message    | None                                 |
  | project_id | cf5a8f5cc5834d2dacd1d54cd0a354b7     |
  | status     | PENDING                              |
  | updated_at | None                                 |
  | version    | 1                                    |
  | zone_id    | None                                 |
  +------------+--------------------------------------+

You can now view the zone in Designate:

.. code-block:: console

  $ openstack recordset list example.org.
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+
  | id                                   | name              | type | records                                                             | status | action |
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+
  | 3d9e96c2-da27-4c5b-9b2b-c1b44a58c1e5 | www.example.org.  | A    | 192.0.2.2                                                           | ACTIVE | NONE   |
  |                                      |                   |      | 192.0.2.1                                                           |        |        |
  | 541bac15-18da-411f-a8e5-8ccecb65ae1f | example.org.      | SOA  | ns1.example.org. admin.example.org. 1624415706 3541 600 86400 3600  | ACTIVE | NONE   |
  | a643b088-6052-49c0-81f7-6ade6682d9a3 | example.org.      | NS   | ns1.example.org.                                                    | ACTIVE | NONE   |
  | f97274f1-e062-4f59-8ec0-11bccd830547 | test.example.org. | A    | 192.0.2.100                                                         | ACTIVE | NONE   |
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+

You cannot use zone imports to update a zone or create records in a zone that
already exists. Importing a zone that already exists will result in an error
and no records will be created or modified.

.. code-block:: console

  $ echo "new.example.org. IN A 192.0.2.101" >> zone_file
  $ openstack zone import create zone_file
  +------------+--------------------------------------+
  | Field      | Value                                |
  +------------+--------------------------------------+
  | created_at | 2021-06-24T03:40:28.000000           |
  | id         | 50516762-23ec-4bf3-a065-530171c5d0fb |
  | message    | None                                 |
  | project_id | cf5a8f5cc5834d2dacd1d54cd0a354b7     |
  | status     | PENDING                              |
  | updated_at | None                                 |
  | version    | 1                                    |
  | zone_id    | None                                 |
  +------------+--------------------------------------+
  $ openstack zone import show 50516762-23ec-4bf3-a065-530171c5d0fb
  +------------+--------------------------------------+
  | Field      | Value                                |
  +------------+--------------------------------------+
  | created_at | 2021-06-24T03:40:28.000000           |
  | id         | 50516762-23ec-4bf3-a065-530171c5d0fb |
  | message    | An undefined error occurred.         |
  | project_id | cf5a8f5cc5834d2dacd1d54cd0a354b7     |
  | status     | ERROR                                |
  | updated_at | 2021-06-24T03:40:28.000000           |
  | version    | 2                                    |
  | zone_id    | None                                 |
  +------------+--------------------------------------+
  $ openstack recordset list example.org.
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+
  | id                                   | name              | type | records                                                             | status | action |
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+
  | 3d9e96c2-da27-4c5b-9b2b-c1b44a58c1e5 | www.example.org.  | A    | 192.0.2.2                                                           | ACTIVE | NONE   |
  |                                      |                   |      | 192.0.2.1                                                           |        |        |
  | 541bac15-18da-411f-a8e5-8ccecb65ae1f | example.org.      | SOA  | ns1.example.org. admin.example.org. 1624415706 3541 600 86400 3600  | ACTIVE | NONE   |
  | a643b088-6052-49c0-81f7-6ade6682d9a3 | example.org.      | NS   | ns1.example.org.                                                    | ACTIVE | NONE   |
  | f97274f1-e062-4f59-8ec0-11bccd830547 | test.example.org. | A    | 192.0.2.100                                                         | ACTIVE | NONE   |
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+

You must set the zone TTL using a TTL statement in the zone tile.
The SOA record created for the zone will not always match the values in the
zone file as some values are dependent on Designate configuration options:

- The `MNAME` is set using the zone's assigned pool information.
- The refresh value is set randomly between the ``default_soa_refresh_min``
  and ``default_soa_refresh_max`` configuration values.
- The minimum value is set to the ``soa_default_minimum`` configuration value.

The NS record for the zone is generated based on the pool the zone has been
assigned. Other NS records are imported without modification.

For example, the following zone file uses `test.example.org.` as its namserver,
and provides its own values for the zone TTL, refresh, minimum and expire. The
refresh and minimum values will be discarded on import and the nameserver
changed to the pool's nameserver at `ns1.example.org.`:

.. code-block:: console

  $ cat zone_file
  $ORIGIN example.org.
  $TTL 3000

  example.org.  IN NS test.example.org.
  example.org.  IN SOA test.example.org. admin.example.org. 1624415706 9000 500 86000 5000
  www.example.org.  IN A 192.0.2.2
  test.example.org.  IN NS test.example.org.
  $ openstack zone import create zone_file
  +------------+--------------------------------------+
  | Field      | Value                                |
  +------------+--------------------------------------+
  | created_at | 2021-06-25T07:07:41.000000           |
  | id         | ccd0af00-aa5f-43e0-a57d-67cfa2f3738e |
  | message    | None                                 |
  | project_id | cf5a8f5cc5834d2dacd1d54cd0a354b7     |
  | status     | PENDING                              |
  | updated_at | None                                 |
  | version    | 1                                    |
  | zone_id    | None                                 |
  +------------+--------------------------------------+
  $ openstack recordset list example.org.
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+
  | id                                   | name              | type | records                                                             | status | action |
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+
  | 35143297-5268-4bc9-80bb-9d2d12c609e0 | example.org.      | SOA  | ns1.example.org. admin.example.org. 1624415706 3582 500 86000 3600  | ACTIVE | NONE   |
  | 3532dee3-effc-4aac-b5c4-90b6e2ad20e0 | test.example.org. | NS   | test.example.org.                                                   | ACTIVE | NONE   |
  | bef04729-f49e-4920-83b6-2ef9b620fa9d | example.org.      | NS   | ns1.example.org.                                                    | ACTIVE | NONE   |
  | c290d79a-6583-4666-a6f7-d4b967f67d79 | www.example.org.  | A    | 192.0.2.2                                                           | ACTIVE | NONE   |
  +--------------------------------------+-------------------+------+---------------------------------------------------------------------+--------+--------+

.. _RFC 1892: https://datatracker.ietf.org/doc/html/rfc1982
.. _zone file format: https://en.wikipedia.org/wiki/Zone_file
