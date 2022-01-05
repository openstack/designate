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

================================
How to install DNS with DevStack
================================

The Designate source code contains a DevStack plugin that allows to deploy
an OpenStack installation with the DNS service enabled.

Instructions
~~~~~~~~~~~~

.. note::

    If you want to use local sources for development then you should consider
    using the contrib/vagrant folder in the
    `repository <https://opendev.org/openstack/designate>`_.

1. Get a clean Ubuntu 20.04 VM (see the `DevStack installation
   instructions`_ for more details). DevStack "takes over". Don't use
   your desktop!

.. _`DevStack installation instructions`: https://docs.openstack.org/devstack/latest/#install-linux

2. Clone DevStack inside the VM

   .. code-block:: console

      $ git clone https://opendev.org/openstack/devstack.git

3. Move to ``devstack`` directory

   .. code-block:: console

      $ cd devstack

4. Create a `local.conf` config file

   .. literalinclude:: ../../../contrib/vagrant/local.conf
      :language: bash

5. Run DevStack

   .. code-block:: console

      $ ./stack.sh

6. See the status of all Designate processes

   .. code-block:: console

      $ sudo systemctl status devstack@designate-*.service

   See the `Using Systemd in DevStack`_ home page for more options.

.. _`Using Systemd in DevStack`: https://docs.openstack.org/devstack/latest/systemd.html

7. Querying Logs

   .. code-block:: console

      $ sudo journalctl -f --unit devstack@designate-*.service

   See the `Querying Logs`_ home page for more options.

.. _`Querying Logs`: https://docs.openstack.org/devstack/latest/systemd.html#querying-logs

8. Load credentials into the shell

   .. code-block:: console

      $ export OS_CLOUD=devstack-admin   # For the admin user, admin project
      $ export OS_CLOUD=devstack         # For the demo user, demo project

9. Try out the openstack client

   .. code-block:: console

      $ openstack zone create --email admin@example.net example.net.
      +----------------+--------------------------------------+
      | Field          | Value                                |
      +----------------+--------------------------------------+
      | action         | CREATE                               |
      | attributes     |                                      |
      | created_at     | 2017-11-15T04:48:40.000000           |
      | description    | None                                 |
      | email          | admin@example.net                    |
      | id             | f34f835b-9acc-4930-b6dd-d045c15da78a |
      | masters        |                                      |
      | name           | example.net.                         |
      | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
      | project_id     | 9d0beaef253a4e14bd7025dc30c24f98     |
      | serial         | 1510721320                           |
      | status         | PENDING                              |
      | transferred_at | None                                 |
      | ttl            | 3600                                 |
      | type           | PRIMARY                              |
      | updated_at     | None                                 |
      | version        | 1                                    |
      +----------------+--------------------------------------+

      $ openstack recordset create --record '127.0.0.1'  --type A example.net. www
      +-------------+--------------------------------------+
      | Field       | Value                                |
      +-------------+--------------------------------------+
      | action      | CREATE                               |
      | created_at  | 2017-11-15T04:51:27.000000           |
      | description | None                                 |
      | id          | 7861e600-8d9e-4e13-9ea2-9038a2719b41 |
      | name        | www.example.net.                     |
      | project_id  | 9d0beaef253a4e14bd7025dc30c24f98     |
      | records     | 127.0.0.1                            |
      | status      | PENDING                              |
      | ttl         | None                                 |
      | type        | A                                    |
      | updated_at  | None                                 |
      | version     | 1                                    |
      | zone_id     | f34f835b-9acc-4930-b6dd-d045c15da78a |
      | zone_name   | example.net.                         |
      +-------------+--------------------------------------+

      $ openstack recordset list f34f835b-9acc-4930-b6dd-d045c15da78a
      +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+
      | id                                   | name             | type | records                                                             | status | action |
      +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+
      | d0630d94-94d8-43fc-93e8-973fbec7531e | example.net.     | SOA  | ns1.devstack.org. admin.example.net. 1510721487 3510 600 86400 3600 | ACTIVE | NONE   |
      | 31a313dc-c322-4dc0-ba53-79c039d7f09f | example.net.     | NS   | ns1.devstack.org.                                                   | ACTIVE | NONE   |
      | 7861e600-8d9e-4e13-9ea2-9038a2719b41 | www.example.net. | A    | 127.0.0.1                                                           | ACTIVE | NONE   |
      +--------------------------------------+------------------+------+---------------------------------------------------------------------+--------+--------+

      $ openstack recordset show f34f835b-9acc-4930-b6dd-d045c15da78a 7861e600-8d9e-4e13-9ea2-9038a2719b41
      +-------------+--------------------------------------+
      | Field       | Value                                |
      +-------------+--------------------------------------+
      | action      | NONE                                 |
      | created_at  | 2017-11-15T04:51:27.000000           |
      | description | None                                 |
      | id          | 7861e600-8d9e-4e13-9ea2-9038a2719b41 |
      | name        | www.example.net.                     |
      | project_id  | 9d0beaef253a4e14bd7025dc30c24f98     |
      | records     | 127.0.0.1                            |
      | status      | ACTIVE                               |
      | ttl         | None                                 |
      | type        | A                                    |
      | updated_at  | None                                 |
      | version     | 1                                    |
      | zone_id     | f34f835b-9acc-4930-b6dd-d045c15da78a |
      | zone_name   | example.net.                         |
      +-------------+--------------------------------------+

10. Verify that the ``recordset`` is in DNS

    .. code-block:: console

       $ dig www.example.net @${SERVICE_HOST}

       ; <<>> DiG 9.16.1-Ubuntu <<>> www.example.net @192.168.27.100
       ;; global options: +cmd
       ;; Got answer:
       ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 34315
       ;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
       ;; WARNING: recursion requested but not available

       ;; OPT PSEUDOSECTION:
       ; EDNS: version: 0, flags:; udp: 4096
       ; COOKIE: f10292dba9100bbf010000005f749e3586096307a693d0fe (good)
       ;; QUESTION SECTION:
       ;www.example.net.               IN      A

       ;; ANSWER SECTION:
       www.example.net.        3600    IN      A       127.0.0.1

       ;; Query time: 0 msec
       ;; SERVER: 192.168.27.100#53(192.168.27.100)
       ;; WHEN: Wed Sep 30 15:03:17 UTC 2020
       ;; MSG SIZE  rcvd: 88

    where ``SERVICE_HOST`` is the IP address used in ``local.conf``.
