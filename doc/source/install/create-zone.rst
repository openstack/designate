.. _create-zone:

Create a Zone
~~~~~~~~~~~~~

In environments that include the DNS service, you can create a DNS Zone.

#. Source the ``demo`` credentials to perform
   the following steps as a non-administrative project:

   .. code-block:: console

      $ . demo-openrc

#. Create a DNS Zone called ``example.com.``:

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

#. After a short time, verify successful creation of the DNS Zone:

   .. code-block:: console

      $ openstack zone list
      +--------------------------------------+--------------+---------+------------+--------+--------+
      | id                                   | name         | type    |     serial | status | action |
      +--------------------------------------+--------------+---------+------------+--------+--------+
      | 14093115-0f0f-497a-ac69-42235e46c26f | example.com. | PRIMARY | 1468421656 | ACTIVE | NONE   |
      +--------------------------------------+--------------+---------+------------+--------+--------+

#. You can now create RecordSets in this DNS Zone:

   .. code-block:: console

      $ openstack recordset create --record '10.0.0.1' --type A example.com. www
      +-------------+--------------------------------------+
      | Field       | Value                                |
      +-------------+--------------------------------------+
      | action      | CREATE                               |
      | created_at  | 2016-07-13T14:59:32.000000           |
      | description | None                                 |
      | id          | 07e6f5af-783e-481f-b8df-5972a6174c94 |
      | name        | www.example.com.                     |
      | project_id  | 656bc359067844fba6005d400f19df76     |
      | records     | 10.0.0.1                             |
      | status      | PENDING                              |
      | ttl         | None                                 |
      | type        | A                                    |
      | updated_at  | None                                 |
      | version     | 1                                    |
      | zone_id     | 14093115-0f0f-497a-ac69-42235e46c26f |
      | zone_name   | example.com.                         |
      +-------------+--------------------------------------+

#. Delete the DNS Zone:

   .. code-block:: console

      $ openstack zone delete example.com.
      +----------------+--------------------------------------+
      | Field          | Value                                |
      +----------------+--------------------------------------+
      | action         | DELETE                               |
      | attributes     |                                      |
      | created_at     | 2017-07-12T03:26:25.000000           |
      | description    | None                                 |
      | email          | dnsmaster@example.com                |
      | id             | 4a21a893-2c58-4797-82ed-19fcef7c418d |
      | masters        |                                      |
      | name           | example.com.                         |
      | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
      | project_id     | d53f80b5a22b4962a176935eea23f9c4     |
      | serial         | 1499830029                           |
      | status         | PENDING                              |
      | transferred_at | None                                 |
      | ttl            | 3600                                 |
      | type           | PRIMARY                              |
      | updated_at     | 2017-07-12T03:27:25.000000           |
      | version        | 4                                    |
      +----------------+--------------------------------------+
