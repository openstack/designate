..
    Copyright 2013 Rackspace Hosting

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _getting-started:

===============
Getting Started
===============

Designate is comprised of three designate components :ref:`designate-api`, :ref:`designate-central` and :ref:`designate-sink`, supported by a few standard open source components. For more information see :doc:`architecture`.

There are many different options for customizing Designate, and two of these options
have a major impact on the installation process:

* The storage backend used (SQLite or MySQL)
* The DNS backend used (PowerDNS or BIND)

This guide will walk you through setting up a typical development environment for Designate,
using PowerDNS as the DNS backend and MySQL as the storage backend. For a more complete discussion on
installation & configuration options, please see :doc:`architecture` and :doc:`production-architecture`.

For this guide you will need access to an Ubuntu Server (12.04).  Other platforms:

- `Fedora 19 Notes`_

.. _Development Environment:

Development Environment
+++++++++++++++++++++++

Installing Designate
====================

.. index::
   double: install; designate

1. Install system package dependencies (Ubuntu)

::

   $ apt-get install python-pip python-virtualenv
   $ apt-get install rabbitmq-server
   $ apt-get build-dep python-lxml

2. Clone the Designate repo from GitHub

::

   $ git clone https://github.com/openstack/designate.git
   $ cd designate


3. Setup virtualenv

.. note::
   This is an optional step, but will allow Designate's dependencies
   to be installed in a contained environment that can be easily deleted
   if you choose to start over or uninstall Designate.

::

   $ virtualenv --no-site-packages .venv
   $ . .venv/bin/activate


4. Install Designate and its dependencies

::

   $ pip install -r requirements.txt -r test-requirements.txt
   $ python setup.py develop


5. Change directories to the etc/designate folder.

.. note::
    Everything from here on out should take place in or below your designate/etc folder

::

   $ cd etc/designate


6. Create Designate's config files by copying the sample config files

::

   $ ls *.sample | while read f; do cp $f $(echo $f | sed "s/.sample$//g"); done


7. Make the directory for Designate’s log files

::

   $ mkdir /var/log/designate


Configuring Designate
======================

.. index::
    double: configure; designate

Open the designate.conf file for editing

::

  $ editor designate.conf


Copy or mirror the configuration from this sample file here:

.. literalinclude:: examples/basic-config-sample.conf
    :language: ini

Installing MySQL
================

.. index::
    double: install; mysql

Install the MySQL server package

::

    $ apt-get install mysql-server-5.5


If you do not have MySQL previously installed, you will be prompted to change the root password.
By default, the MySQL root password for Designate is "password". You can:

* Change the root password to "password"
* If you want your own password, edit the designate.conf file and change any instance of
   "mysql://root:password@127.0.0.1/designate" to "mysql://root:YOUR_PASSWORD@127.0.0.1/designate"

You can change your MySQL password anytime with the following command::

    $ mysqladmin -u root -p password NEW_PASSWORD
    Enter password <enter your old password>

Create the Designate and PowerDNS tables

::

    $ mysql -u root -p
    Enter password: <enter your password here>

    mysql> CREATE DATABASE `designate` CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql> CREATE DATABASE `powerdns` CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql> exit;


Install additional packages

::

    $ apt-get install libmysqlclient-dev
    $ pip install mysql-python


Installing PowerDNS
===================

.. index::
    double: install; powerdns

Install the DNS server, PowerDNS

::

      $ DEBIAN_FRONTEND=noninteractive apt-get install pdns-server pdns-backend-mysql

      #Update MySQL database info
      $ editor /etc/powerdns/pdns.d/pdns.local.gmysql

      #Change the corresponding lines in the config file:
      gmysql-dbname=powerdns
      gmysql-user=root
      gmysql-password=password
      #If you're using your own root password, use 'gmysql-password=YOUR_PASSWORD'

      #Restart PowerDNS:
      $ service pdns restart


If you intend to run Designate as a non-root user, then sudo permissions need to be granted

::

   $ echo "designate ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/90-designate
   $ sudo chmod 0440 /etc/sudoers.d/90-designate


Initialize & Start the Central Service
======================================

.. index::
   double: install; central

::

   #Sync the Designate database:
   $ designate-manage database sync

   #Sync the PowerDNS database:
   $ designate-manage powerdns sync

   #Restart PowerDNS
   $ service pdns restart

   #Start the central service:
   $ designate-central

.. note::
   If you get an error of the form: ERROR [designate.openstack.common.rpc.common] AMQP server on localhost:5672 is unreachable: Socket closed

   Run the following command:

::

   $ rabbitmqctl change_password guest guest

   #Then try starting the service again
   $ designate-central

You'll now be seeing the log from the central service.

Initialize & Start the API Service
==================================

.. index::
   double: install; api

Open up a new ssh window and log in to your server (or however you’re communicating with your server).

::

   $ cd root/designate
   #Make sure your virtualenv is sourced
   $ . .venv/bin/activate
   $ cd etc/designate
   #Start the API Service
   $ designate-api
   #You may have to run root/designate/bin/designate-api

You’ll now be seeing the log from the API service.

Exercising the API
==================

.. note:: If you have a firewall enabled, make sure to open port 53, as well as Designate's default port (9001).

Using a web browser, curl statement, or a REST client, calls can be made to the Designate API using the following format where “command” is any of the commands listed in the :doc:`rest`

.. _Designate REST Documentation:

http://IP.Address:9001/v1/command

You can find the IP Address of your server by running

::

   wget http://ipecho.net/plain -O - -q ; echo

A couple of notes on the API:

- Before Domains are created, you must create a server.
- On GET requests for domains, servers, records, etc be sure not to append a ‘/’ to the end of the request. For example …:9001/v1/servers/

Fedora 19 Notes
===============

Most of the above instructions under `Installing Designate`_ should work.  There are a few differences when working with Fedora 19:

Installing Designate
--------------------

Installing the basic Fedora packages needed to install Designate:

::

   $ yum install gcc git yum-utils
   $ yum install python-pip python-virtualenv python-pbr rabbitmq-server
   $ yum-builddep python-lxml

Use **/var/lib/designate** as the root path for databases and other variable state files, not /root/designate

::

   $ mkdir -p /var/lib/designate

Installing MySQL
----------------

The MySQL Fedora packages are **mysql mysql-server mysql-devel**

::

    $ yum install mysql mysql-server mysql-devel
    $ pip install mysql-python

You will have to change the MySQL password manually.

::

    $ systemctl start mysqld.service
    $ mysqladmin -u root password NEW_PASSWORD
        # default password for Designate is 'password'

Installing PowerDNS
-------------------

The PowerDNS Fedora packages are **pdns pdns-backend-mysql**

::

   $ yum install pdns pdns-backend-mysql

Fedora 19 does not use /etc/powerdns/pdns.d.  Instead, edit **/etc/pdns/pdns.conf** - change the launch option, and add a gmysql-database option

::

   ...
   setuid=pdns
   setgid=pdns
   launch=gmysql
   gmysql-host=127.0.0.1
   gmysql-user=root
   gmysql-password=password
   gmysql-dbname=powerdns
   ...

Fedora uses **systemctl**, not service

::

   $ systemctl [start|restart|stop|status] pdns.service
   $ systemctl [start|restart|stop|status] rabbitmq-server.service

Configuring RabbitMQ
--------------------

The rabbitmq service must be running before doing

::

   $ rabbitmqctl change_password guest guest

RabbitMQ may fail to start due to SELinux.  Use *journalctl -xn|cat* to find the error.  You will likely have to do something like this until it is added to the SELinux base policy

::

   $ yum install /usr/bin/checkpolicy
   $ grep beam /var/log/audit/audit.log|audit2allow -M mypol
   $ semodule -i mypol.pp
   $ systemctl start rabbitmq-server.service

The rabbitmq log files are in **/var/log/rabbitmq**
