.. _production-architecture:

=============================
Production Architecture
=============================

Outline
-------
This document outlines what a production environment hosting Designate could look like, it follows an in-cloud model, where Designate would be hosted on instances in an OpenStack cloud.  It's supposed to complement the
:doc:`architecture` document, please start there if you are unfamiliar with the designate components.

Designate Dependencies
----------------------
Designate has been designed to integrate with Keystone, or a Keystone-like service, for authentication & authorization, in a production environment it should rely on your Keystone service, and
be registered in your service catalog.

Expectations
------------
This architecture expects your environment to have an external loadbalancer that is the first touch point for customer traffic, this will distribute requests across the available API nodes,
which should span your AZs & regions where possible.

Roles
-----
A Designate deploy breaks down into several key roles:

- `Designate API`_
- `Designate Sink`_
- `Designate Central`_
- `Designate MiniDNS`_
- `Designate Pool Manager`_
- `Message Queue`_
- `Database`_ (MySQL or derivative)
- `Memory caching`_
- `DNS Backend`_

Designate API
~~~~~~~~~~~~~~~~~~~
Typically, API nodes would be made available in multiple AZs, providing redundancy should an individual AZ have issues.

In a Multi-AZ deployment, the API nodes should be configured to talk to all members of the MQ Cluster - so that in the event of MQ node failing, requests continue to flow to the MQ.

Designate Sink
~~~~~~~~~~~~~~~~~~~~~~~
In a Multi-AZ deployment, the sink node should be configured to talk to all members of the MQ Cluster - so that in the event of MQ node failing, requests continue to flow to the MQ.

Designate Central
~~~~~~~~~~~~~~~~~~~~~~~
In a Multi-AZ deployment, the Central nodes should be configured to talk to all members of the MQ Cluster - so that in the event of MQ node failing, requests continue to be processed.

Designate MiniDNS
~~~~~~~~~~~~~~~~~~~~~~~
In a Multi-AZ deployment, the MiniDNS nodes should be configured to talk to all members of the MQ Cluster - so that in the event of MQ node failing, requests continue to be processed. It should also be configured to talk to multiple DB servers, to allow for reliable access to the data store

Designate Pool Manager
~~~~~~~~~~~~~~~~~~~~~~~
In a Multi-AZ deployment, the Pool Manager nodes should be configured to talk to all members of the MQ Cluster - so that in the event of MQ node failing, requests continue to be processed.

Message Queue
~~~~~~~~~~~~~
An AMQP implementation is required for all communication between api & central nodes, in practice this means an RabbitMQ installation, preferably a cluster that spans across the AZs in a given region.

Database
~~~~~~~~~~~~~~~~
Designate needs a SQLAlchemy supported :ref:`database` engine for the persistent storage of data, the recommended driver is MySQL.

In a Multi-AZ environment, a MySQL Galera Cluster, built using Percona's MySQL packages has performed well.

Memory Caching
~~~~~~~~~~~~~~
Designate optionally uses :ref:`memory-caching-summary` usually through a Memcached instance to speed up Pool Manager operations.

DNS Backend
~~~~~~~~~~~
Designate supports multiple backend implementations, PowerDNS, BIND and MySQL BIND, you are also free to implement your own backend to fit your needs, as well as extensions to provide extra functionality to complement existing backends.

There are various ways to provide a highly available authoritative DNS service, here are some suggestions:

* Multiple PowerDNS instances using the same database being maintained by :ref:`designate-central`, optionally using MySQL Replication to propagate the data to multiple locations.
* DNS AXFR (Zone Transfer) multiple slave DNS server get notified of zone updates from a DNS server being managed by :ref:`designate-central`.

