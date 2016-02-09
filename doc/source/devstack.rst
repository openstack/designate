..
    Copyright 2013 Hewlett-Packard Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _devstack:

========
DevStack
========

The Designate team maintains a fork of devstack with Designate integration.

Instructions
++++++++++++

.. note::

    If you want to use local sources for development then you should consider
    using the contrib/vagrant folder in the
    `repository <https://git.openstack.org/openstack/designate>`_.

1. Get a clean Ubuntu 14.04 VM. DevStack "takes over". Don't use your desktop!

2. Clone DevStack inside the VM::

   $ git clone https://git.openstack.org/openstack-dev/devstack.git

3. Move to ``devstack`` directory::

   $ cd devstack

4. Create a `local.conf` config file:

   .. literalinclude:: ../../contrib/vagrant/local.conf
       :language: bash

5. Run DevStack::

   $ ./stack.sh

6. Enter the screen sessions "shell" window::

   $ ./rejoin-stack.sh

   Then press Ctrl+A followed by 0

7. Load credentials into the shell::

   $ source openrc admin admin # For the admin user, admin tenant
   $ source openrc admin demo  # For the admin user, demo tenant
   $ source openrc demo demo   # For the demo user, demo tenant

8. Try out the designate client::

       $ designate domain-create --name example.net. --email kiall@hp.com
       +------------+--------------------------------------+
       | Field      | Value                                |
       +------------+--------------------------------------+
       | name       | example.net.                         |
       | created_at | 2013-07-12T13:36:03.110727           |
       | updated_at | None                                 |
       | id         | 1fb5d17c-efaf-4e3c-aac0-482875d24b3e |
       | ttl        | 3600                                 |
       | serial     | 1373636163                           |
       | email      | kiall@hp.com                         |
       +------------+--------------------------------------+

       $ designate record-create 1fb5d17c-efaf-4e3c-aac0-482875d24b3e --type A --name www.example.net. --data 127.0.0.1
       +------------+--------------------------------------+
       | Field      | Value                                |
       +------------+--------------------------------------+
       | name       | www.example.net.                     |
       | data       | 127.0.0.1                            |
       | created_at | 2013-07-12T13:39:51.236025           |
       | updated_at | None                                 |
       | id         | d50c21d0-a13c-48e2-889e-0b9852a05acb |
       | priority   | None                                 |
       | ttl        | None                                 |
       | type       | A                                    |
       | domain_id  | 1fb5d17c-efaf-4e3c-aac0-482875d24b3e |
       +------------+--------------------------------------+

       $ designate record-list 1fb5d17c-efaf-4e3c-aac0-482875d24b3e
       +--------------------------------------+------+------------------+
       | id                                   | type | name             |
       +--------------------------------------+------+------------------+
       | d50c21d0-a13c-48e2-889e-0b9852a05acb | A    | www.example.net. |
       +--------------------------------------+------+------------------+

       $ designate record-get 1fb5d17c-efaf-4e3c-aac0-482875d24b3e d50c21d0-a13c-48e2-889e-0b9852a05acb
       +------------+--------------------------------------+
       | Field      | Value                                |
       +------------+--------------------------------------+
       | name       | www.example.net.                     |
       | data       | 127.0.0.1                            |
       | created_at | 2013-07-12T13:39:51.000000           |
       | updated_at | None                                 |
       | id         | d50c21d0-a13c-48e2-889e-0b9852a05acb |
       | priority   | None                                 |
       | ttl        | None                                 |
       | type       | A                                    |
       | domain_id  | 1fb5d17c-efaf-4e3c-aac0-482875d24b3e |
       +------------+--------------------------------------+
