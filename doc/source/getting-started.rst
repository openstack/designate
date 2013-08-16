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

========================
Getting Started
========================

Designate is comprised of three designate components :ref:`designate-api`, :ref:`designate-central` and :ref:`designate-sink`, supported by a few standard open source components. For more info see :doc:`architecture`.

This guide will walk you through setting up a development environment for Designate, using PowerDNS as the DNS
backend, where possible the simplest options have been chosen for you.  For a more complete discussion on
installation & configuration options, please see :doc:`architecture` and :doc:`production-architecture`.

For this guide you will need access to an Ubuntu Server (12.04).

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

2. Clone the Designate repo off of Stackforge

::

   $ git clone https://github.com/stackforge/designate.git
   $ cd designate


3. Setup virtualenv

.. note::
   This is to not interfere with system packages etc.

::

   $ virtualenv --no-site-packages .venv
   $ . .venv/bin/activate

4. Install Designate and its dependencies

::

   $ pip install -r requirements.txt -r test-requirements.txt
   $ python setup.py develop


.. note::
   Everything from here on out should take place in or below your designate/etc folder

5. Copy sample config files to edit

::

   $ cd etc/designate
   $ ls *.sample | while read f; do cp $f $(echo $f | sed "s/.sample$//g"); done

6. Install the DNS server, PowerDNS

::

      $ DEBIAN_FRONTEND=noninteractive apt-get install pdns-server pdns-backend-sqlite3
      #Update path to SQLite database to /root/designate/pdns.sqlite or wherever your top level designate directory resides
      $ editor /etc/powerdns/pdns.d/pdns.local.gsqlite3
      #Change the corresponding line in the config file to mirror:
      gsqlite3-database=/root/designate/pdns.sqlite
      #Restart PowerDNS:
      $ service pdns restart


7. If you intend to run Designate as a non-root user, then sudo permissions need to be granted

::

   $ echo "designate ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/90-designate
   $ sudo chmod 0440 /etc/sudoers.d/90-designate

8. Make the directory for Designate’s log files

::

   $ mkdir /var/log/designate

Configure Designate
===================

.. index::
   double: configure; designate

::

  $ editor designate.conf

Copy or mirror the configuration from this sample file here:

.. literalinclude:: examples/basic-config-sample.conf
   :language: ini

Initialize & Start the Central Service
======================================

.. index::
   double: install; central

::

   #Initialize and sync the Designate database:
   $ designate-manage database-init
   $ designate-manage database-sync
   #Initialize and sync the PowerDNS database:
   $ designate-manage powerdns database-init
   $ designate-manage powerdns database-sync
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
Using a web browser, curl statement, or a REST client calls can be made to the Designate API using the following format where “command” is any of the commands listed in the :doc:`rest`

.. _Designate REST Documentation:

http://IP.Address:9001/v1/command

You can find the IP Address of your server by running

::

   wget http://ipecho.net/plain -O - -q ; echo

A couple of notes on the API:

- Before Domains are created, you must create a server.
- On GET requests for domains, servers, records, etc be sure not to append a ‘/’ to the end of the request. For example …:9001/v1/servers/

