..
    Copyright 2020 Cloudification GmbH.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Shared Zones
============

Shared zones allow sharing a particular zone across tenants. This is
useful in cases when records for one zone should be managed by
multiple projects. For example when a Designate zone is assigned to a
shared network in Neutron.

Zone shares have the following properties:

- Quotas will be enforced against the zone owner.
- Projects that a zone is shared with can only manage recordsets created or
  owned by the project.
- Zone owners can see, modify, and remove recordsets created by another
  project.
- Projects that a zone is shared with cannot see or modify the attributes of
  the zone.
- Zones that have shares cannot be deleted without removing the shares or using
  the `delete-shares` modifier.
- Projects that a zone is shared with cannot create sub-zones.

How to Share a Zone With Another Project
----------------------------------------

Create a zone to share:

.. code-block:: console

    $ openstack zone create example.com. --email admin@example.com
    +----------------+--------------------------------------+
    | Field          | Value                                |
    +----------------+--------------------------------------+
    | action         | CREATE                               |
    | email          | admin@example.com                    |
    | id             | 92b2214f-8a57-4ed3-95f0-a64099f3b516 |
    | name           | example.com.                         |
    | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
    | project_id     | 804806ad94364aecb0f9ae86ad653055     |
    | serial         | 1596186919                           |
    | status         | PENDING                              |
    | ttl            | 3600                                 |
    | type           | PRIMARY                              |
    +----------------+--------------------------------------+


Share the zone using the `openstack zone share create` command
(in this example, the ID of the project we want to share with is
`356df8e6c7564b5bb107f5de26cdb8ea`):

.. code-block:: console

    $ openstack zone share create example.com. 356df8e6c7564b5bb107f5de26cdb8ea
    +-------------------+--------------------------------------+
    | Field             | Value                                |
    +-------------------+--------------------------------------+
    | created_at        | 2023-01-30T23:17:44.000000           |
    | id                | 77e4d5b9-2057-4be7-8cf0-9f84ef0efec1 |
    | project_id        | 804806ad94364aecb0f9ae86ad653055     |
    | target_project_id | 356df8e6c7564b5bb107f5de26cdb8ea     |
    | updated_at        | None                                 |
    | zone_id           | 92b2214f-8a57-4ed3-95f0-a64099f3b516 |
    +-------------------+--------------------------------------+


Project `356df8e6c7564b5bb107f5de26cdb8ea` now has access to zone
`92b2214f-8a57-4ed3-95f0-a64099f3b516` and can manage recordsets in the zone.

Using credentials for project `356df8e6c7564b5bb107f5de26cdb8ea`, we can create
a recordset for `www.example.com.`:

.. code-block:: console

    $ openstack recordset create --type A --record 192.0.2.1 example.com. www
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | action      | CREATE                               |
    | created_at  | 2023-01-30T23:28:05.000000           |
    | description | None                                 |
    | id          | aff3e00a-9e5c-4cfa-9650-65196f73418b |
    | name        | www.example.com.                     |
    | project_id  | 356df8e6c7564b5bb107f5de26cdb8ea     |
    | records     | 192.0.2.1                            |
    | status      | PENDING                              |
    | ttl         | None                                 |
    | type        | A                                    |
    | updated_at  | None                                 |
    | version     | 1                                    |
    | zone_id     | 92b2214f-8a57-4ed3-95f0-a64099f3b516 |
    | zone_name   | example.com.                         |
    +-------------+--------------------------------------+


How to List All of the Projects Sharing a Zone
----------------------------------------------

You can list all of the zone shares for a zone with the `openstack zone share
list` command:

.. code-block:: console

    $ openstack zone share list example.com.
    +-----------------------+-----------------------+-------------------------+
    | id                    | zone_id               | target_project_id       |
    +-----------------------+-----------------------+-------------------------+
    | 77e4d5b9-2057-4be7-   | 92b2214f-8a57-4ed3-   | 356df8e6c7564b5bb107f5d |
    | 8cf0-9f84ef0efec1     | 95f0-a64099f3b516     | e26cdb8ea               |
    +-----------------------+-----------------------+-------------------------+


How To Remove a Zone Share
--------------------------

To stop sharing a zone with a project, you can use the `openstack zone share
delete` command:

.. code-block:: console

    $ openstack zone share delete example.com. 77e4d5b9-2057-4be7-8cf0-9f84ef0efec1

A zone cannot be unshared in the following cases:

- Zone has recordsets in other projects.
