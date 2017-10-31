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

.. _backend-powerdns:

PowerDNS Backend
================

.. warning:: This backend will not work with PowerDNS version 4 or greater. Use the ``pdns4`` backend.



PowerDNS Configuration
----------------------

You need to configure PowerDNS to use the MySQL backend.

1. First enable the MySQL backend:

.. code-block:: ini

    launch = gmysql

2. Configure the MySQL database settings:

.. code-block:: ini

    gmysql-host=<host>
    gmysql-port=
    gmysql-dbname=<dbname>
    gmysql-user=<username>
    gmysql-password=<password>
    gmysql-dnssec=yes
    #gmysql-socket=<socket path>


.. note::
   PowerDNS can connect via socket or host/port.

3. Configure the PowerDNS Backend using this sample target snippet

.. literalinclude:: sample_yaml_snippets/powerdns.yaml
   :language: yaml

4. Then update the pools in designate

.. code-block:: console

    $ designate-manage pool update

See :ref:`designate_manage_pool` for further details on
the ``designate-manage pool`` command, and :ref:`pools`
for information about the yaml file syntax

4. Setup the database schema.

.. code-block:: console

    $ designate-manage powerdns sync <pool_id>

See :ref:`designate_manage_powerdns` for further details on
the ``designate-manage powerdns`` command

5. Restart PowerDNS and it should be ready to serve queries
   using the MySQL database as the backing store.

