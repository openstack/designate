****************************
Installing Liberty on Ubuntu
****************************

This section describes how to install Designate on Ubuntu 14.04.
To install other OpenStack services, see `OpenStack Installation
Guide <http://docs.openstack.org/#install-guides>`_.
This section assumes the Identity service runs on the host
``controller``.

Install and configure Basic Environment
=======================================

Enable OpenStack repository
---------------------------

#. Enable the OpenStack Liberty repository:

   .. code-block:: console

      $ sudo apt-get update
      $ sudo apt-get install software-properties-common
      $ sudo add-apt-repository cloud-archive:liberty

#. Upgrade the packages on your host:

   .. code-block:: console

      $ sudo apt-get update
      $ sudo apt-get dist-upgrade

Install and configure SQL database
----------------------------------

#. Install the MariaDB packages:

   .. code-block:: console

      $ sudo apt-get install mariadb-server python-pymysql

   Choose a suitable password for the database root account.

Install and configure message queue
-----------------------------------

#. Install the RabbitMQ packages:

   .. code-block:: console

      $ sudo apt-get install rabbitmq-server

#. Add the ``openstack`` user:

   .. code-block:: console

      $ sudo rabbitmqctl add_user openstack RABBIT_PASS
      Creating user "openstack" ...

   Replace ``RABBIT_PASS`` with a suitable password.

#. Permit configuration, write, and read access for the ``openstack`` user:

   .. code-block:: console

      $ sudo rabbitmqctl set_permissions openstack ".*" ".*" ".*"
      Setting permissions for user "openstack" in vhost "/" ...

Install DNS server
==================

#. Install the BIND9 packages:

   .. code-block:: console

      $ sudo apt-get install bind9

#. Add the following options in the ``/etc/bind/named.conf.options`` file:

   .. code-block:: none

      options {
          ...
          allow-new-zones yes;
          request-ixfr no;
          recursion no;
      };

#. Restart the DNS service:

   .. code-block:: console

      $ sudo service bind9 restart

Install Designate
=================

#. Install the ``designate`` package:

   .. code-block:: console

      $ sudo apt-get install designate

#. In the ``Configuring designate-common`` prompt,
   complete the following actions:

   * select ``Yes`` for the question ``Set up a database for Designate?``.
   * enter ``localhost`` for the ``IP address of your RabbitMQ host``.
   * enter the ``openstack`` as ``Username for connection to the RabbitMQ
     server``.
   * enter the ``password for connection to the RabbitMQ server``
     that you chose for the RabbitMQ server at the previous step.
   * press the ``enter`` key at the prompt ``Authentication server hostname``.
   * press the ``enter`` key at the prompt ``Authentication server password``.
   * select ``No`` for the question ``Register Designate in the Keystone
     endpoint catalog?``.
   * select ``Yes`` for the question ``Configure database for
     designate-common with dbconfig-common``.
   * select ``mysql`` for ``database type to be used by designate-common``.
   * enter the ``password of the database's administrative user``
     that is chosen for the root account at the previous step.
   * enter the ``MySQL application password for designate-common``.
   * enter the same password as ``password confirmation``.

.. note::

   the ``designate-common`` package offers automatic creation of the
   database tables for Designate during the installation process.

Configure Designate
===================

#. Source the admin credentials to gain access to admin-only CLI commands.

#. Create the ``designate`` user:

   .. code-block:: console

      $ openstack user create --domain default --password-prompt designate
      User Password:
      Repeat User Password:
      +-----------+----------------------------------+
      | Field     | Value                            |
      +-----------+----------------------------------+
      | domain_id | default                          |
      | enabled   | True                             |
      | id        | b7dd483c69654442b09a7458f7daf8d3 |
      | name      | designate                        |
      +-----------+----------------------------------+

#. Add the admin role to the ``designate`` user and ``service`` project:

   .. code-block:: console

      $ openstack role add --project service --user designate admin

#. Create the ``designate`` service entity:

   .. code-block:: console

      $ openstack service create --name designate \
        --description "OpenStack DNS service" dns
      +-------------+----------------------------------+
      | Field       | Value                            |
      +-------------+----------------------------------+
      | description | OpenStack DNS service            |
      | enabled     | True                             |
      | id          | 6f634693062946579f678c32c006e097 |
      | name        | designate                        |
      | type        | dns                              |
      +-------------+----------------------------------+

#. Create the DNS service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        dns public http://controller:9001
      +--------------+----------------------------------+
      | Field        | Value                            |
      +--------------+----------------------------------+
      | enabled      | True                             |
      | id           | 05bf0535afad4e0897fcbc4686bf1ab9 |
      | interface    | public                           |
      | region       | RegionOne                        |
      | region_id    | RegionOne                        |
      | service_id   | 6f634693062946579f678c32c006e097 |
      | service_name | designate                        |
      | service_type | dns                              |
      | url          | http://controller:9001           |
      +--------------+----------------------------------+

      $ openstack endpoint create --region RegionOne \
        dns internal http://controller:9001
      +--------------+----------------------------------+
      | Field        | Value                            |
      +--------------+----------------------------------+
      | enabled      | True                             |
      | id           | b8f56bf8a8ed4e88b1655655a3327ae6 |
      | interface    | internal                         |
      | region       | RegionOne                        |
      | region_id    | RegionOne                        |
      | service_id   | 6f634693062946579f678c32c006e097 |
      | service_name | designate                        |
      | service_type | dns                              |
      | url          | http://controller:9001           |
      +--------------+----------------------------------+

      $ openstack endpoint create --region RegionOne \
        dns admin http://controller:9001
      +--------------+----------------------------------+
      | Field        | Value                            |
      +--------------+----------------------------------+
      | enabled      | True                             |
      | id           | f081aef76b06472cb791aa04d920f195 |
      | interface    | admin                            |
      | region       | RegionOne                        |
      | region_id    | RegionOne                        |
      | service_id   | 6f634693062946579f678c32c006e097 |
      | service_name | designate                        |
      | service_type | dns                              |
      | url          | http://controller:9001           |
      +--------------+----------------------------------+

#. Edit the ``/etc/designate/designate.conf`` file and
   complete the following actions:

   * In the ``[service:api]`` section, configure ``auth_strategy``:

     .. code-block:: ini

        [service:api]
        api_host = 0.0.0.0
        api_port = 9001
        auth_strategy = keystone
        enable_api_v1 = True
        enabled_extensions_v1 = diagnostics, quotas, reports, sync, touch
        enable_api_v2 = True
        enabled_extensions_v2 = quotas, reports

   * In the ``[keystone_authtoken]`` section, configure the following options:

     .. code-block:: ini

        [keystone_authtoken]
        auth_host = controller
        auth_port = 35357
        auth_protocol = http
        admin_tenant_name = service
        admin_user = designate
        admin_password = DESIGNATE_PASS

     Replace DESIGNATE_PASS with the password you chose for the ``designate``
     user in the Identity service.

   * In the ``[service:pool_manager]`` section, configure ``pool_id``:

     .. code-block:: ini

        [service:pool_manager]
        pool_id = 794ccc2c-d751-44fe-b57f-8894c9f5c842

   * Configure the pool:

     .. code-block:: ini

        [pool:794ccc2c-d751-44fe-b57f-8894c9f5c842]
        nameservers = 0f66b842-96c2-4189-93fc-1dc95a08b012
        targets = f26e0b32-736f-4f0a-831b-039a415c481e

        [pool_nameserver:0f66b842-96c2-4189-93fc-1dc95a08b012]
        port = 53
        host = 127.0.0.1

        [pool_target:f26e0b32-736f-4f0a-831b-039a415c481e]
        options = port: 53, host: 127.0.0.1
        masters = 127.0.0.1:5354
        type = bind9

   * In the ``[storage:sqlalchemy]`` section, configure database access:

     .. code-block:: ini

        [storage:sqlalchemy]
        connection = mysql+pymysql://designate-common:DESIGNATE_DBPASS@localhost/designatedb

     ``DESIGNATE_DBPASS`` is automatically set to the password
     you chose for the Designate database.

   * In the ``[pool_manager_cache:sqlalchemy]`` section, configure database access:

     .. code-block:: ini

        [pool_manager_cache:sqlalchemy]
        connection = mysql+pymysql://designate-common:DESIGNATE_DBPASS@localhost/designate_pool_manager

     Replace ``DESIGNATE_DBPASS`` with a suitable password.

#. Restart the Designate central and API services:

   .. code-block:: console

      $ sudo service designate-central restart
      $ sudo service designate-api restart

Install Designate pool manager and mdns
=======================================

#. Create the ``designate_pool_manager`` database and grant proper access:

   .. code-block:: console

      $ mysql -u root -p
      Enter password: <enter your root password here>

      mysql> CREATE DATABASE `designate_pool_manager` CHARACTER SET utf8 COLLATE utf8_general_ci;
      mysql> GRANT ALL PRIVILEGES ON designate_pool_manager.* TO 'designate-common'@'localhost'
             IDENTIFIED BY 'DESIGNATE_DBPASS';
      mysql> exit;

#. Install the ``designate-pool-manager`` and ``designate-mdns`` package:

   .. code-block:: console

      $ sudo apt-get install designate-pool-manager designate-mdns

#. Sync the Pool Manager cache:

   .. code-block:: console

      $ sudo su -s /bin/sh -c "designate-manage pool-manager-cache sync" designate

#. Restart the Designate pool manager and mDNS services:

   .. code-block:: console

      $ sudo service designate-pool-manager restart
      $ sudo service designate-mdns restart

Verify operation
================

.. note::

   If you have a firewall enabled, make sure to open port 53,
   as well as Designate's default port (9001).

Using a web browser, curl statement, or a REST client, calls can be made
to the Designate API using the following format where "api_version" is
either v1 or v2 and "command" is any of the commands listed under the
corresponding version at :ref:`rest`.

::

   http://controller:9001/api_version/command

You can find the IP Address of your server by running:

::

   curl -s checkip.dyndns.org | sed -e 's/.*Current IP Address: //' -e 's/<.*$//'

.. note::

   Before Domains are created, you must create a server (/v1/servers).
