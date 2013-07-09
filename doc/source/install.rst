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

Designate is comprised of three components for more info on these please
see :doc:`architecture`.

.. note::
   Designate makes extensive use of the messaging bus, but has not
   yet been tested with ZeroMQ. We recommend using RabbitMQ for now.


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
   $ apt-get install rabbitmq-server
   $ apt-get build-dep python-lxml

2. Clone the Designate repo off of Stackforge::

   $ git clone https://github.com/stackforge/designate.git
   $ cd designate

3. Setup virtualenv::

.. note::
   This is to not interfere with system packages etc.

   $ virtualenv --no-site-packages .venv
   $ . .venv/bin/activate

4. Install Designate and it's dependencies::

   $ cd designate
   $ pip install -r requirements.txt -r test-requirements.txt
   $ python setup.py develop

   Copy sample config files::

   $ cd etc/designate
   $ ls *.sample | while read f; do cp $f $(echo $f | sed "s/.sample$//g"); done

5. Install a DNS server::

   1. PowerDNS (recommended)::

      Install PowerDNS::

      $ DEBIAN_FRONTEND=noninteractive apt-get install pdns-server pdns-backend-sqlite3

      Update path to SQLite database to `$CHECKOUT_PATH/powerdns.sqlite`::

      $ editor /etc/powerdns/pdns.d/pdns.local.gsqlite3

      Restart PowerDNS::

      $ service pdns restart

   2. BIND9::

      Install BIND9::

      $ apt-get install bind9

      Include the Designate managed zones::

      $ editor /etc/bind/named.conf

      Add the following line to the file::

        include "$CHECKOUT_PATH/bind9/zones.config"

      Disable AppArmor for BIND9::

      $ touch /etc/apparmor.d/disable/usr.sbin.named
      $ service apparmor reload

      Restart BIND9::

      $ service bind9 restart

7. If you intend to run Designate as a non-root user, then sudo permissions
   need to be granted::

   $ echo "designate ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/90-designate
   $ sudo chmod 0440 /etc/sudoers.d/90-designate

8. Configure the common settings::

   Change the necessary configuration settings in the DEFAULT section, the file
   is in the `etc/designate` folder::

   $ editor designate.conf

   Refer to :doc:`configuration` details on configuring the service.

Note on running processes
=========================

You can start each of the processes mentioned below in for example a screen
session to view output


Installing the Central Service
==============================

.. index::
   double: installing; central

1. See `Common Steps`_ before proceeding.

2. Configure the :term:`central` service::

   Change the necessary configuration settings in the service:central,
   storage:sqlalchemy sections and, optionally the backend:powerdns section::

   $ editor designate.conf

   Refer to :doc:`configuration` details on configuring the service.

   .. note::
      Pay particular attention to the "backend_driver" setting, along with the
      two sql_connection strings for service:central, and backend:powerdns.

      These *must* point at different databases.

3. Initialize and sync the Designate database::

   $ designate-manage database-init
   $ designate-manage database-sync

4. Initialize and sync the PowerDNS database, if necessay::

   $ designate-manage powerdns database-init
   $ designate-manage powerdns database-sync

5. Start the central service::

   $ designate-central


Installing the Agent Service
============================

.. index::
   double: installing; agent

.. note::
   The agent service is only required when zone configuration must be "manually"
   propagated to multiple servers. For example, remote BIND9 instances needs to,
   at the very least, know about all of the zones it is responsible for.

   For the purposes of a single BIND9 quickstart.. You can skip this service.

   If you use PowerDNS, this service can always be skipped.


1. See `Common Steps`_ before proceeding.

2. Configure the :term:`agent` service::

   Change the necessary configuration settings in the service:agent,
   and backend:bind9 sections::

   $ editor designate.conf

   Refer to :doc:`configuration` details on configuring the service.

3. Start the agent service::

   $ designate-agent


Installing the API Service
==========================

.. index::
   double: installing; api

.. note::
   The API Server needs to able to talk to Keystone for AuthN + Z and
   communicates via MQ to other services.

1. See `Common Steps`_ before proceeding.

2. Configure the :term:`api` service::

   Change the necessary configuration settings in the service:api section::

   $ editor designate.conf

   .. note::
      Pay particular attention to the "auth_strategy" setting, "noauth" disables
      all authentication, and keystone requires setup in the api-paste.

   If using the keystone auth_strategy, change the necessary configuration
   settings in the paste deploy config::

   $ editor api-paste.conf

   Refer to :doc:`configuration` details on configuring the service.

3. Start the API service::

   $ designate-api
