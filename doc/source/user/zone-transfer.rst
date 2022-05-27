..
    Copyright 2022 Red Hat

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

========================
Zone Ownership Transfers
========================

Designate allows you to transfer ownership of zones between projects. For
example, the engineering team project may want to transfer the ownership of the
'wow.example.com.' zone from the engineering project to the marketing team's
project.

This can be accomplished without cloud administrator intervention using the
zone transfer features in Designate. Both the sending and receiving project
must agree to the transfer by using the zone transfer process.

Zone Transfer Requests
======================

Creating a Zone Transfer Request
--------------------------------

To create a zone transfer offer we create a zone transfer request in Designate.
You can optionally provide a target project ID in the request to lock the
transfer to a specific project. When using a target project ID, no other
project will be allowed to accept the zone transfer. If you do not provide a
target project ID, any project that has the transfer request ID and key can
receive the zone transfer.

.. note::

    The target project ID must be provided as the ``ID`` and not the project
    name.

To transfer the zone 'wow.example.com.' to project
1d12e87fad0d437286c2873b36a12316 you would run:

.. code-block:: console

    $ openstack zone transfer request create --target-project-id 1d12e87fad0d437286c2873b36a12316 wow.example.com.

    +-------------------+-----------------------------------------------------+
    | Field             | Value                                               |
    +-------------------+-----------------------------------------------------+
    | created_at        | 2022-05-26T22:06:39.000000                          |
    | description       | None                                                |
    | id                | 63cab5e5-65fa-4480-b26c-c16c267c44b2                |
    | key               | BIFJIQWH                                            |
    | links             | {'self': 'http://127.0.0.1:60053/v2/zones/tasks/tra |
    |                   | nsfer_requests/63cab5e5-65fa-4480-b26c-c16c267c44b2 |
    |                   | '}                                                  |
    | project_id        | 6265985fc493465db6a978b318a01996                    |
    | status            | ACTIVE                                              |
    | target_project_id | 1d12e87fad0d437286c2873b36a12316                    |
    | updated_at        | None                                                |
    | zone_id           | 962f08b4-b671-4096-bf24-8908c9d4af0c                |
    | zone_name         | wow.example.com.                                    |
    +-------------------+-----------------------------------------------------+

You will then provide the ID and key to a member of the receiving project.

Displaying a Zone Transfer Request
----------------------------------

To display the zone transfer request we created in the previous section you
would run:

.. code-block:: console

    $ openstack zone transfer request show 63cab5e5-65fa-4480-b26c-c16c267c44b2

    +-------------------+-----------------------------------------------------+
    | Field             | Value                                               |
    +-------------------+-----------------------------------------------------+
    | created_at        | 2022-05-26T22:06:39.000000                          |
    | description       | None                                                |
    | id                | 63cab5e5-65fa-4480-b26c-c16c267c44b2                |
    | key               | BIFJIQWH                                            |
    | links             | {'self': 'http://127.0.0.1:60053/v2/zones/tasks/tra |
    |                   | nsfer_requests/63cab5e5-65fa-4480-b26c-c16c267c44b2 |
    |                   | '}                                                  |
    | project_id        | 6265985fc493465db6a978b318a01996                    |
    | status            | ACTIVE                                              |
    | target_project_id | 1d12e87fad0d437286c2873b36a12316                    |
    | updated_at        | None                                                |
    | zone_id           | 962f08b4-b671-4096-bf24-8908c9d4af0c                |
    | zone_name         | wow.example.com.                                    |
    +-------------------+-----------------------------------------------------+

Listing Zone Transfer Requests
------------------------------

You can list all of the existing zone transfer requests by using the
`openstack zone transfer request list` command:

.. code-block:: console

    $ openstack zone transfer request list

    +----------+----------+-----------+------------+-------------------+--------+----------+
    | id       | zone_id  | zone_name | project_id | target_project_id | status | key      |
    +----------+----------+-----------+------------+-------------------+--------+----------+
    | 63cab5e5 | 962f08b4 | wow.examp | 6265985fc4 | 1d12e87fad0d43728 | ACTIVE | BIFJIQWH |
    | -65fa-44 | -b671-40 | le.com.   | 93465db6a9 | 6c2873b36a12316   |        |          |
    | 80-b26c- | 96-bf24- |           | 78b318a019 |                   |        |          |
    | c16c267c | 8908c9d4 |           | 96         |                   |        |          |
    | 44b2     | af0c     |           |            |                   |        |          |
    +----------+----------+-----------+------------+-------------------+--------+----------+

Updating a Zone Transfer Request
--------------------------------

Designate allows you to update a limited set of fields on zone transfer
requests, such as the description and target project ID.

To add a description the zone transfer request we created above, you would run
the following command:

.. code-block:: console

    $ openstack zone transfer request set --description "wow zone transfer" 63cab5e5-65fa-4480-b26c-c16c267c44b2

    +-------------------+-----------------------------------------------------+
    | Field             | Value                                               |
    +-------------------+-----------------------------------------------------+
    | created_at        | 2022-05-26T22:06:39.000000                          |
    | description       | wow zone transfer                                   |
    | id                | 63cab5e5-65fa-4480-b26c-c16c267c44b2                |
    | key               | BIFJIQWH                                            |
    | links             | {'self': 'http://127.0.0.1:60053/v2/zones/tasks/tra |
    |                   | nsfer_requests/63cab5e5-65fa-4480-b26c-c16c267c44b2 |
    |                   | '}                                                  |
    | project_id        | 6265985fc493465db6a978b318a01996                    |
    | status            | ACTIVE                                              |
    | target_project_id | 1d12e87fad0d437286c2873b36a12316                    |
    | updated_at        | 2022-05-27T20:52:08.000000                          |
    | zone_id           | 962f08b4-b671-4096-bf24-8908c9d4af0c                |
    | zone_name         | wow.example.com.                                    |
    +-------------------+-----------------------------------------------------+

Deleting a Zone Transfer Request
--------------------------------

If you would like to cancel a zone transfer you can delete the zone transfer
request using the `openstack zone transfer request delete` command:

.. code-block:: console

    $ openstack zone transfer request delete 63cab5e5-65fa-4480-b26c-c16c267c44b2

There is no output from the zone transfer request delete command.

Zone Transfer Accepts
=====================

Accepting a Zone Transfer Request
---------------------------------

Once you have the zone transfer request ID and key, you can create a
`zone transfer accept` to finish the zone transfer.

An example of accepting the zone transfer we created in the
`Zone Transfer Requests`_ section:

.. code-block:: console

    $ openstack zone transfer accept request --transfer-id 63cab5e5-65fa-4480-b26c-c16c267c44b2 --key BIFJIQWH

    +--------------------------+----------------------------------------------+
    | Field                    | Value                                        |
    +--------------------------+----------------------------------------------+
    | created_at               | 2022-05-27T21:37:43.000000                   |
    | id                       | a4c4f872-c98c-411b-a787-58ed0e2dce11         |
    | key                      | BIFJIQWH                                     |
    | links                    | {'self': 'http://127.0.0.1:60053/v2/zones/ta |
    |                          | sks/transfer_accepts/a4c4f872-c98c-411b-a787 |
    |                          | -58ed0e2dce11', 'zone': 'http://127.0.0.1:60 |
    |                          | 053/v2/zones/962f08b4-b671-4096-bf24-8908c9d |
    |                          | 4af0c'}                                      |
    | project_id               | 1d12e87fad0d437286c2873b36a12316             |
    | status                   | COMPLETE                                     |
    | updated_at               | 2022-05-27T21:37:43.000000                   |
    | zone_id                  | 962f08b4-b671-4096-bf24-8908c9d4af0c         |
    | zone_transfer_request_id | 63cab5e5-65fa-4480-b26c-c16c267c44b2         |
    +--------------------------+----------------------------------------------+

Displaying a Zone Transfer Accept
---------------------------------

To check the status of your zone transfer accept, you can use the
`openstack zone transfer accept` command:

.. code-block:: console

    $ openstack zone transfer accept show a4c4f872-c98c-411b-a787-58ed0e2dce11

    +--------------------------+----------------------------------------------+
    | Field                    | Value                                        |
    +--------------------------+----------------------------------------------+
    | created_at               | 2022-05-27T21:37:43.000000                   |
    | id                       | a4c4f872-c98c-411b-a787-58ed0e2dce11         |
    | key                      | None                                         |
    | links                    | {'self': 'http://127.0.0.1:60053/v2/zones/ta |
    |                          | sks/transfer_accepts/a4c4f872-c98c-411b-a787 |
    |                          | -58ed0e2dce11', 'zone': 'http://127.0.0.1:60 |
    |                          | 053/v2/zones/962f08b4-b671-4096-bf24-8908c9d |
    |                          | 4af0c'}                                      |
    | project_id               | 1d12e87fad0d437286c2873b36a12316             |
    | status                   | COMPLETE                                     |
    | updated_at               | 2022-05-27T21:37:43.000000                   |
    | zone_id                  | 962f08b4-b671-4096-bf24-8908c9d4af0c         |
    | zone_transfer_request_id | 63cab5e5-65fa-4480-b26c-c16c267c44b2         |
    +--------------------------+----------------------------------------------+

Listing Zone Transfer Accepts
-----------------------------

Designate can provide a list of existing zone transfer accept records using the
`openstack zone transfer accept list` command:

.. note::

    By default, only users with the 'admin' role can list zone transfer accept
    records.

.. code-block:: console

    $ openstack zone transfer accept list

    +-------------+-------------+-------------+--------------------------+----------+-----+
    | id          | zone_id     | project_id  | zone_transfer_request_id | status   | key |
    +-------------+-------------+-------------+--------------------------+----------+-----+
    | a4c4f872-c9 | 962f08b4-b6 | 1d12e87fad0 | 63cab5e5-65fa-4480-b26c- | COMPLETE |     |
    | 8c-411b-a78 | 71-4096-bf2 | d437286c287 | c16c267c44b2             |          |     |
    | 7-58ed0e2dc | 4-8908c9d4a | 3b36a12316  |                          |          |     |
    | e11         | f0c         |             |                          |          |     |
    +-------------+-------------+-------------+--------------------------+----------+-----+
