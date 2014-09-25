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

Designate Configuration
-----------------------

===============================  ====================================== ==============================================================
Parameter                        Default                                Note
===============================  ====================================== ==============================================================
domain_type                      NATIVE                                 PowerDNS Domain Type
also_notify                      []                                     List of additional IPs to send NOTIFYs to.
connection                       sqlite:///$pystatepath/powerdns.sqlite Database connection string
connection_debug                 0                                      Verbosity of SQL debugging information. 0=None, 100=Everything
connection_trace                 False                                  Add python stack traces to SQL as comment strings
idle_timeout                     3600                                   timeout before idle sql connections are reaped
max_retries                      10                                     maximum db connection retries during startup.
                                                                        (setting -1 implies an infinite retry count)
retry_interval                   10                                     interval between retries of opening a sql connection
mysql_engine                     InnoDB                                 MySQL engine to use
sqlite_synchronous               True                                   If passed, use synchronous mode for sqlite
===============================  ====================================== ==============================================================


PowerDNS Configuration
----------------------

You need to configure PowerDNS to use the MySQL backend.

1. First enable the MySQL backend:

    launch = gmysql

2. Configure the MySQL database settings::

    gmysql-host=<host>
    gmysql-port=
    gmysql-dbname=<dbname>
    gmysql-user=<username>
    gmysql-password=<password>
    gmysql-dnssec=yes
    #gmysql-socket=<socket path>

.. note::
   PowerDNS can connect via socket or host/port.

3. Configure the options for designate-central - specifaclly "connection" to point to your MySQL database::

    [backend:powerdns]
    connection = mysql://<username>:<password>@<host>:<port>/<dbname>

4. Setup the database schema.

::

    $ designate-manage powerdns init
    $ designate-manage powerdns sync

5. Restart PowerDNS and it should be ready to serve queries using the MySQL database as the backing store.


PowerDNS deployment as hidden Master
------------------------------------

One deployment scenario can be that the PowerDNS backend will be used as a "hidden" Master DNS for other DNS servers to consume via AXFR.

Say you have 10.0.0.1 and 10.0.0.2 as slaves then configure the backend as follows in addition to other options::

    [backend:powernds]
    domain_type = MASTER
    also_notify = 10.0.0.1,10.0.0.2

.. note::
   This should mostly be used in connection with another backend acting as slave.
