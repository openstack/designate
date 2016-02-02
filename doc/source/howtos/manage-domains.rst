..
    Copyright 2015 Hewlett-Packard Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

How To Create and Manage Domains
================================

Install Client
--------------

To install Designate client, see `OpenStack Command-Line Interface Reference
<http://docs.openstack.org/cli-reference/overview.html>`_.

Create and View Domains
-----------------------

To create a new domain, a minimum of two pieces of information are required:

+-------+---------------------------------------------------------------------------+
| Name  | Description                                                               |
+=======+===========================================================================+
| Name  | The name of the domain you are creating. The name must end with a period. |
+-------+---------------------------------------------------------------------------+
| Email | An email address of the person responsible for the domain.                |
+-------+---------------------------------------------------------------------------+

Create the domain
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ designate domain-create --name designate-example.com. --email designate@example.org
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | description | None                                 |
    | created_at  | 2015-02-13T16:23:26.533547           |
    | updated_at  | None                                 |
    | email       | designate@example.org                |
    | ttl         | 3600                                 |
    | serial      | 1423844606                           |
    | id          | ae59d62b-d655-49a0-ab4b-ea536d845a32 |
    | name        | designate-example.com.               |
    +-------------+--------------------------------------+

List the Servers Hosting a Domain
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
   This list of servers are the "nameservers" you must provide to your domain
   registrar in order to delegate the domain to Designate. Without performing
   this step, the domain and records created will not resolve.

.. code-block:: bash

    $ designate domain-servers-list ae59d62b-d655-49a0-ab4b-ea536d845a32
    +------------------+
    | name             |
    +------------------+
    | ns1.example.org. |
    | ns2.example.org. |
    | ns3.example.org. |
    +------------------+

List and Show Domains
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ designate domain-list
    +--------------------------------------+-------------------------------------------+------------+
    | id                                   | name                                      |     serial |
    +--------------------------------------+-------------------------------------------+------------+
    | ae59d62b-d655-49a0-ab4b-ea536d845a32 | designate-example.com.                    | 1423844606 |
    +--------------------------------------+-------------------------------------------+------------+

    $ designate domain-get ae59d62b-d655-49a0-ab4b-ea536d845a32
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | description | None                                 |
    | created_at  | 2015-02-13T16:23:26.000000           |
    | updated_at  | None                                 |
    | email       | designate@example.org                |
    | ttl         | 3600                                 |
    | serial      | 1423844606                           |
    | id          | ae59d62b-d655-49a0-ab4b-ea536d845a32 |
    | name        | designate-example.com.               |
    +-------------+--------------------------------------+

Create and View Records
-----------------------

To create a new record in the domain, a minimum of four pieces of information are required:

+-----------+-----------------------------------------------------------+
| Name      | Description                                               |
+===========+===========================================================+
| Domain ID | The Domain ID which the record will belong to.            |
+-----------+-----------------------------------------------------------+
| Name      | The fully qualified record name to create.                |
+-----------+-----------------------------------------------------------+
| Type      | The record type to be created (e.g: A, AAAA, MX etc).     |
+-----------+-----------------------------------------------------------+
| Data      | The type specific value to be associated with the record. |
+-----------+-----------------------------------------------------------+

Create the Record
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ designate record-create ae59d62b-d655-49a0-ab4b-ea536d845a32 --name www.designate-example.com. --type A --data 192.0.2.1
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | description | None                                 |
    | type        | A                                    |
    | created_at  | 2015-02-13T16:43:10.952601           |
    | updated_at  | None                                 |
    | domain_id   | ae59d62b-d655-49a0-ab4b-ea536d845a32 |
    | priority    | None                                 |
    | ttl         | None                                 |
    | data        | 192.0.2.1                            |
    | id          | 10b31f72-2358-466c-90d2-79aa015fbea4 |
    | name        | www.designate-example.com.           |
    +-------------+--------------------------------------+

List and Show Records
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ designate record-list ae59d62b-d655-49a0-ab4b-ea536d845a32
    +--------------------------------------+------+----------------------------+-----------+
    | id                                   | type | name                       | data      |
    +--------------------------------------+------+----------------------------+-----------+
    | 10b31f72-2358-466c-90d2-79aa015fbea4 | A    | www.designate-example.com. | 192.0.2.1 |
    +--------------------------------------+------+----------------------------+-----------+

    $ designate record-get ae59d62b-d655-49a0-ab4b-ea536d845a32 10b31f72-2358-466c-90d2-79aa015fbea4
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | description | None                                 |
    | type        | A                                    |
    | created_at  | 2015-02-13T16:43:10.000000           |
    | updated_at  | None                                 |
    | domain_id   | ae59d62b-d655-49a0-ab4b-ea536d845a32 |
    | priority    | None                                 |
    | ttl         | None                                 |
    | data        | 192.0.2.1                            |
    | id          | 10b31f72-2358-466c-90d2-79aa015fbea4 |
    | name        | www.designate-example.com.           |
    +-------------+--------------------------------------+
