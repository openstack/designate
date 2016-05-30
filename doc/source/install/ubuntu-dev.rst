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

*********************************
Development Environment on Ubuntu
*********************************

Designate is comprised of four main components :ref:`designate-api`, :ref:`designate-central`,
:ref:`designate-mdns`, and :ref:`designate-pool-manager`, supported by a few
standard open source components. For more information see :ref:`architecture`.

There are many different options for customizing Designate, and two of these options
have a major impact on the installation process:

* The storage backend used (SQLite or MySQL)
* The DNS backend used (PowerDNS or BIND9)

This guide will walk you through setting up a typical development environment for Designate,
using BIND9 as the DNS backend and MySQL as the storage backend. For a more complete discussion on
installation & configuration options, please see :ref:`architecture` and :ref:`production-architecture`.

For this guide you will need access to an Ubuntu Server (14.04).

.. _Development Environment:

Development Environment
+++++++++++++++++++++++

Installing Designate
====================

.. index::
   double: install; designate

1. Install system package dependencies (Ubuntu)

::

   $ sudo apt-get update
   $ sudo apt-get install python-pip python-virtualenv libssl-dev libffi-dev git
   $ sudo apt-get build-dep python-lxml

2. Clone the Designate repo from GitHub

::

   $ mkdir openstack
   $ cd openstack
   $ git clone https://git.openstack.org/openstack/designate.git
   $ cd designate


3. Setup a virtualenv

.. note::
   This step is necessary to allow the installation of an up-to-date
   pip, independent of the version packaged for Ubuntu. it is 
   also useful in isolating the remainder of Designate's dependencies
   from the rest of the system.

::

   $ virtualenv .venv
   $ . .venv/bin/activate

4. Install an up-to-date pip

::

   $ pip install -U pip


5. Install Designate and its dependencies

.. note::
   If you run into the error: Installed distribution pbr 1.1.1 conflicts with requirement pbr>=0.6,!=0.7,<1.0, try doing pip install pbr==0.11.0

::

   $ pip install -r requirements.txt -r test-requirements.txt
   $ python setup.py develop


6. Change directories to the etc/designate folder.

.. note::
    Everything from here on out should take place in or below your designate/etc folder

::

   $ cd etc/designate


7. Create Designate's config files by copying the sample config files

::

   $ cp -a rootwrap.conf.sample rootwrap.conf


8. Make the directory for Designate’s log files

::

   $ mkdir -p ../../log


9. Make the directory for Designate’s state files

::

   $ mkdir -p ../../state



Configuring Designate
======================

.. index::
    double: configure; designate

Create the designate.conf file

::

  $ editor designate.conf


Copy or mirror the configuration from this sample file here:

.. literalinclude:: ../examples/basic-config-sample.conf
    :language: ini


Installing RabbitMQ
===================

Install the RabbitMQ package

::

    $ sudo apt-get install rabbitmq-server

Create a user:

::

    $ sudo rabbitmqctl add_user designate designate

Give the user access to the / vhost:

::

    $ sudo rabbitmqctl set_permissions -p "/" designate ".*" ".*" ".*"


Installing MySQL
================

.. index::
    double: install; mysql

Install the MySQL server package

::

    $ sudo apt-get install mysql-server-5.5


If you do not have MySQL previously installed, you will be prompted to change the root password.
By default, the MySQL root password for Designate is "password". You can:

* Change the root password to "password"
* If you want your own password, edit the designate.conf file and change any instance of
   "mysql+pymysql://root:password@127.0.0.1/designate?charset=utf8" to "mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1/designate?charset=utf8"

You can change your MySQL password anytime with the following command::

    $ mysqladmin -u root -p password NEW_PASSWORD
    Enter password <enter your old password>

Create the Designate tables

::

    $ mysql -u root -p
    Enter password: <enter your password here>

    mysql> CREATE DATABASE `designate` CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql> CREATE DATABASE `designate_pool_manager` CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql> exit;


Install additional packages

::

    $ sudo apt-get install libmysqlclient-dev
    $ pip install pymysql


Installing BIND9
================

.. index::
    double: install; bind9

Install the DNS server, BIND9

::

    $ sudo apt-get install bind9

Update the BIND9 Configuration

::

    $ sudo editor /etc/bind/named.conf.options

Change the corresponding lines in the config file:

::

    options {
      directory "/var/cache/bind";
      dnssec-validation auto;
      auth-nxdomain no; # conform to RFC1035
      listen-on-v6 { any; };
      allow-new-zones yes;
      request-ixfr no;
      recursion no;
    };

Disable AppArmor for BIND9

::

    $ sudo touch /etc/apparmor.d/disable/usr.sbin.named
    $ sudo service apparmor reload

Restart BIND9:

::

    $ sudo service bind9 restart

Create and Import pools.yml File
================================

.. index::
   double: install; pools

Create the pools.yaml file

::

  $ editor pools.yaml

Copy or mirror the configuration from this sample file here:

.. literalinclude:: ../examples/basic-pools-sample.yaml
    :language: yaml

Import the pools.yaml file into Designate

::

   $ designate-manage pool update --file pools.yaml

Initialize & Start the Central Service
======================================

.. index::
   double: install; central


Sync the Designate database.

::

   $ designate-manage database sync

Start the central service.

::

   $ designate-central


You'll now be seeing the log from the central service.

Initialize & Start the API Service
==================================

.. index::
   double: install; api

Open up a new ssh window and log in to your server (or however you’re communicating with your server).

::

   $ cd openstack/designate

If Designate was installed into a virtualenv, make sure your virtualenv is sourced

::

   $ source .venv/bin/activate

Start the API Service

::

   $ designate-api

You’ll now be seeing the log from the API service.


Initialize & Start the Pool Manager Service
===========================================

.. index::
   double: install; pool-manager

Open up a new ssh window and log in to your server (or however you’re communicating with your server).

::

   $ cd openstack/designate

If Designate was installed into a virtualenv, make sure your virtualenv is sourced

::

   $ source .venv/bin/activate

Sync the Pool Manager's cache:

::

   $ designate-manage pool-manager-cache sync

Start the pool manager service:

::

   $ designate-pool-manager


You'll now be seeing the log from the Pool Manager service.


Initialize & Start the MiniDNS Service
======================================

.. index::
   double: install; minidns

Open up a new ssh window and log in to your server (or however you’re communicating with your server).

::

   $ cd openstack/designate

If Designate was installed into a virtualenv, make sure your virtualenv is sourced

::

   $ source .venv/bin/activate

Start the minidns service:

::

   $ designate-mdns


You'll now be seeing the log from the MiniDNS service.

Exercising the API
==================

.. note:: If you have a firewall enabled, make sure to open port 53, as well as Designate's default port (9001).

Using a web browser, curl statement, or a REST client, calls can be made to the
Designate API using the following format where "api_version" is either v1 or v2
and "command" is any of the commands listed under the corresponding version at :ref:`rest`

::

   http://IP.Address:9001/api_version/command

You can find the IP Address of your server by running

::

   curl -s checkip.dyndns.org | sed -e 's/.*Current IP Address: //' -e 's/<.*$//'

A couple of notes on the API:

- Before Domains are created, you must create a server (/v1/servers).
