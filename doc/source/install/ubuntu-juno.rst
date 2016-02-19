*************************
Installing Juno on Ubuntu
*************************

.. _install-ubuntu-architecture:

Architecture
============


Please see :ref:`production-architecture` for general production architecture notes.

* Ubuntu as the Operating System
* Designate
* RabbitMQ
* MySQL
* :ref:`backend-powerdns`
* Keystone for AuthN / AuthZ (Not included in this guide)


.. _install-ubuntu-prerequisites:

Prerequisites
=============

.. _install-ubuntu-prereq-install:

Install
^^^^^^^
::

    $ sudo apt-get install mysql-server rabbitmq-server pdns-server pdns-backend-mysql

.. _install-ubuntu-prereq-setup-rabbitmq:

RabbitMQ
^^^^^^^^

.. note::

    Do the following commands as "root" or via sudo <command>

Create a user:

::

    $ rabbitmqctl add_user designate designate

Give the user access to the / vhost:

::

    $ sudo rabbitmqctl set_permissions -p "/" designate ".*" ".*" ".*"

.. _install-ubuntu-prereq-setup-mysql:

MySQL
^^^^^

.. note::

    The following commands should be done using the mysql command line or similar.

Create the MySQL user

::

    $ mysql -u root -p
    Enter password: <enter your password here>

    mysql> GRANT ALL ON designate.* TO 'designate'@'localhost' IDENTIFIED BY 'designate';
    mysql> GRANT ALL ON powerdns.* TO 'powerdns'@'localhost' IDENTIFIED BY 'powerdns';

Create the database

::

    mysql> CREATE DATABASE `designate` CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql> CREATE DATABASE `powerdns` CHARACTER SET utf8 COLLATE utf8_general_ci;

.. _install-ubuntu-prereq-pdns:

PowerDNS
^^^^^^^^

Edit the config::

    $ sudo editor /etc/powerdns/pdns.conf

Settings::

    launch = gmysql

Edit the MySQL backend settings::

    $ sudo editor /etc/powerdns/pdns.d/pdns.local.gmysql.conf

Settings::

    gmysql-host=localhost
    gmysql-dbname=powerdns
    gmysql-user=powerdns
    gmysql-password=powerdns

Delete a couple unnecessary files::

    $ rm /etc/powerdns/bindbackend.conf
    $ rm /etc/powerdns/pdns.d/pdns.simplebind.conf

.. _install-ubuntu-source:

Installing using Source (Git)
=============================

1. Install pre-requisites:

::

    $ sudo apt-get install libmysqlclient-dev
    $ sudo apt-get install git python-dev python-pip
    $ sudo apt-get build-dep python-lxml

2. Clone the repository:

::

    $ git clone https://git.openstack.org/openstack/designate designate

3. Change directory to the newly cloned repository

::

     $ cd designate

4. Checking out a specific version:

In some cases you might want to pin the repository version to a specific version of the repository like a stable one.

Example for the Juno release:

::

    $ git checkout stable/juno

3. Install all dependencies using pip

::

    $ sudo pip install -r requirements.txt
    $ sudo pip install MySQL-python

4. Install Designate:

::

    $ sudo python setup.py develop

5. Copy over configuration files

::

    $ sudo cp -R etc/designate /etc/
    $ ls /etc/designate/*.sample | while read f; do sudo cp $f $(echo $f | sed "s/.sample$//g"); done

Create directories
^^^^^^^^^^^^^^^^^^

Since we are not running packages some directories are not created for us.

::

    $ sudo mkdir /var/lib/designate /var/log/designate
    # Needed if you are running designate as a non root user.
    $ sudo chown designate /var/lib/designate /var/log/designate


Configuring
===========

Designate
^^^^^^^^^

::

  $ sudo editor /etc/designate/designate.conf

Copy or mirror the configuration from this sample file here:

.. literalinclude:: /examples/basic-config-sample-juno.conf
   :language: ini

Sync Database schemas
^^^^^^^^^^^^^^^^^^^^^

Initialize and sync the database schemas for Designate and PowerDNS::

    $ designate-manage database sync

    $ designate-manage powerdns sync

Register Designate with Keystone
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For howto register Designate with Keystone you can check the code used in the devstack plugin.

There should be no version registered in the URL for the endpoint.

Starting the services
=====================

Central::

    $ designate-central

API::

    $ designate-api

You should now be able to create zones and use nslookup or dig towards localhost to query pdns for it.
