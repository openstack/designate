..
    Copyright 2012 Endre Karlson for Bouvet ASA

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _install:

========================
Install
========================

Moniker is comprised of three components for more info on these please
see :doc:`architecture`.

.. note::
   Moniker makes extensive use of the messaging bus, but has not
   yet been tested with ZeroMQ. We recommend using RabbitMQ for now.


From Packages
+++++++++++++

From Source / GIT
+++++++++++++++++

Common Steps
============

.. index::
   double: installing; common_steps

.. note::
   The below operations should take place underneath your <project>/etc folder.

1. Install system package dependencies (Ubuntu)::

   $ apt-get install python-pip python-virtualenv
   $ apt-get install rabbitmq-server bind9
   $ apt-get build-dep python-lxml

2. Clone the Moniker repo off of Stackforge::

   $ git clone https://github.com/stackforge/moniker.git
   $ cd moniker

3. Setup virtualenv::

.. note::
   This is to not interfere with system packages etc.

   $ virtualenv --no-site-packages .venv
   $ . .venv/bin/activate

4. Install Moniker and it's dependencies::

   $ cd moniker
   $ pip install -rtools/setup-requires -rtools/pip-requires -rtools/pip-options
   $ python setup.py develop

   Copy sample configs to usable ones, inside the `etc` folder do::

   $ ls *.sample | while read f; do cp $f $(echo $f | sed "s/.sample$//g"); done

5. Configure Bind or other if needed::

   $ vi /etc/bind/named.conf

   Add the following line to the file::

   include "$CHECKOUT_PATH/bind9/zones.config"

6. Restart bind::

   $ sudo service bind9 restart

7. If you intend to run Moniker as a non-root user, then permissions and other
   things needs to be fixed up::

   $ MUSER=username
   $ echo "$MUSER ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/90-moniker-$MUSER
   $ sudo chmod 0440 /etc/sudoers.d/90-moniker-$MUSER


Note on running processes
=========================

You can start each of the processes mentioned below in for example a screen
session to view output


Installing the Central
======================

.. index::
   double: installing; central

1. See `Common Steps`_ before proceeding.

2. Configure the :term:`central` service::

   Change the wanted configuration settings to match your environment, the file
   is in the `etc` folder::

   $ vi moniker-central.conf

   Refer to :doc:`configuration` details on configuring the service.

3. Initialize and sync the :term:`central`::

   $ moniker-manage database-init
   $ moniker-manage database-sync

4. Start the central service::

   $ moniker-central


Installing the Agent
====================

.. index::
   double: installing; agent

1. See `Common Steps`_ before proceeding.

2. Configure the :term:`agent` service::

   Change the wanted configuration settings to match your environment, the file
   is in the `etc` folder::

   $ vi moniker-agent.conf

   Refer to :doc:`configuration` details on configuring the service.

3. Start the agent service::

   $ moniker-agent


Installing the API
====================

.. index::
   double: installing; api

.. note::
   The API Server needs to able to talk to Keystone for AuthN + Z and
   communicates via MQ to other services.

1. See `Common Steps`_ before proceeding.

2. Configure the :term:`api` service::

   Change the wanted configuration settings to match your environment, the file
   is in the `etc` folder::

   $ vi moniker-api.conf
   $ vi moniker-api-paste.ini

   Refer to :doc:`configuration` details on configuring the service.

3. Start the API service::

   $ moniker-api
