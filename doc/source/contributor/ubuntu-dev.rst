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

Designate is comprised of four main components :ref:`designate-api`,
:ref:`designate-central`, designate-mdns, and designate-pool-manager,
supported by a few standard open source components.
For more information see :ref:`architecture`.

There are many different options for customizing Designate, and two of
these options have a major impact on the installation process:

* The storage backend used (SQLite or MySQL)
* The DNS backend used (PowerDNS or BIND9)

This guide will walk you through setting up a typical development environment
for Designate, using BIND9 as the DNS backend and MySQL as the storage
backend. For a more complete discussion on installation & configuration
options, please see :ref:`architecture`.

For this guide you will need access to an Ubuntu Server (16.04).

.. _Development Environment:

Development Environment
+++++++++++++++++++++++

Installing Designate
====================

.. index::
   double: install; designate

1. Install system package dependencies (Ubuntu)

::

   $ sudo apt update
   $ sudo apt install python-pip python-virtualenv libssl-dev libffi-dev git
   $ sudo apt build-dep python-lxml

2. Clone the Designate repo

::

   $ mkdir openstack
   $ cd openstack
   $ git clone https://opendev.org/openstack/designate.git
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

::

   $ pip install -e .


6. Change directories to the etc/designate folder.

.. note::
    Everything from here on out should take place in or below your
    etc/designate folder

::

   $ cd etc/designate


7. Create Designate's config files by copying the sample config files

::

   $ cp -a rootwrap.conf.sample rootwrap.conf


8. Make the directory for Designate's state files

::

   $ mkdir -p ../../state


Configuring Designate
======================

Refer to :ref:`configuration` for a sample configuration options.


Installing RabbitMQ
===================

Install the RabbitMQ package

::

    $ sudo apt install rabbitmq-server

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

    $ sudo apt install mysql-server


If you do not have MySQL previously installed, you will be prompted to change
the root password. By default, the MySQL root password for Designate
is "password". You can:

* Change the root password to "password"
* If you want your own password, edit the designate.conf file and change
  any instance of
  "mysql+pymysql://root:password@127.0.0.1/designate?charset=utf8"
  to "mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1/designate?charset=utf8"

You can change your MySQL password anytime with the following command::

    $ mysqladmin -u root -p password NEW_PASSWORD
    Enter password <enter your old password>

Create the Designate tables

::

    $ mysql -u root -p
    Enter password: <enter your password here>

    mysql> CREATE DATABASE `designate` CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql> exit;


Install additional packages

::

    $ sudo apt install libmysqlclient-dev
    $ pip install pymysql


Installing BIND9
================

.. index::
    double: install; bind9

Install the DNS server, BIND9

::

    $ sudo apt install bind9

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
    $ sudo systemctl reload apparmor

Restart BIND9:

::

    $ sudo systemctl restart bind9

Create and Import pools.yaml File
=================================

.. index::
   double: install; pools

Create the pools.yaml file

::

  $ editor pools.yaml

Copy or mirror the configuration from this sample file here:

.. literalinclude:: ../examples/basic-pools-sample.yaml
    :language: yaml

Initialize the Database
=======================

.. index::
   double: install; database

Sync the Designate database.

::

   $ designate-manage database sync

Start the Central Service
=========================

.. index::
   double: install; central


Start the central service.

::

   $ designate-central


You'll now be seeing the log from the central service.


Initialize Pools Information
============================

Import the pools.yaml file into Designate. It is important that
``designate-central`` is started before invoking this command

::

   $ designate-manage pool update --file pools.yaml


Start the other Services
========================

.. index::
   double: install; services

Open up some new ssh windows and log in to your server
(or open some new screen/tmux sessions).

::

   $ cd openstack/designate
   $ . .venv/bin/activate

Start the other services

::

   $ designate-api
   $ designate-mdns
   $ designate-worker
   $ designate-producer

You'll now be seeing the logs from the other services.

Exercising the API
==================

.. note:: If you have a firewall enabled, make sure to open port 53,
          as well as Designate's default port (9001).

Using a web browser, curl statement, or a REST client, calls can be made to the
Designate API. You can find the various API calls on the api-ref_ document.

For example:

::

   $ curl 127.0.0.1:9001/v2/zones -H 'Content-Type: application/json' --data '
     {
       "name": "example.com.",
       "email": "example@example.com"
     }'

   {"status": "PENDING",.....
   $ curl 127.0.0.1:9001/v2/zones
   {"zones": [{"status": "ACTIVE",.....

The ``ACTIVE`` status shows that the zone propagated. So you should be able to
perform a DNS query and see it:

::

    $ dig @127.0.0.1 example.com SOA +short
    ns1-1.example.org. example.example.com. 1487884120 3531 600 86400 3600

You can find the IP Address of your server by running

::

   ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1

If you have Keystone set up, you can use it by configuring
the ``[keystone_authtoken]`` section and changing
the ``auth_strategy = keystone`` in the ``service:api`` section.
This will make it easier to use clients like the ``openstack``
CLI that expect Keystone.

.. _api-ref: https://docs.openstack.org/api-ref/dns/
