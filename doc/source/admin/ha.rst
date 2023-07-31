.. _ha:

=======================
High Availability Guide
=======================

Designate supports running all of its components services in "active-active"
HA modes.

Some services require some extra setup to ensure that they can work in
active-active, and the services are listed below.

designate-api
=============

Needs Access to:
----------------

* AMQP

.. graphviz::

   digraph APIHA {
     rankdir=LR
     {"L7 Load Balancers" [shape=box]
      "API Server 1" [shape=box]
      "API Server 2" [shape=box]
      "API Server 3" [shape=box]
      "AMQP Servers" [shape=box]
     }
     subgraph "API Servers" {
       cluster=true;
       label="API Servers";
       "API Server 1";
       "API Server 2";
       "API Server 3";
     }
     "L7 Load Balancers" -> {"API Server 1" "API Server 2" "API Server 3"} -> "AMQP Servers";
   }

Notes
-----

To run multiple `designate-api` services, you should run the services behind
a load balancer.

When behind the load balancer, you may need to set the following:

.. code-block:: ini

   [service:api]
   api_base_uri = http://<load balancer URI>/
   enable_host_header = True

Or the following:

.. code-block:: ini

   [oslo_middleware]
   enable_proxy_headers_parsing = true

And then the load balancer to set appropriate headers (e.g. enable `mod_proxy`
in apache.)

designate-central
=================

Needs Access to:
----------------

* AMQP
* Database

.. graphviz::

   digraph CENTRALHA {
     rankdir=LR
     {"AMQP Servers" [shape=box]
      "designate-central Server 1" [shape=box]
      "designate-central Server 2" [shape=box]
      "designate-central Server 3" [shape=box]
      "Database Servers" [shape=cylinder]
     }
     subgraph "designate-central Servers" {
       cluster=true;
       label="designate-central Servers";
       "designate-central Server 1";
       "designate-central Server 2";
       "designate-central Server 3";
     }
     "AMQP Servers" -> "designate-central Server 1" [dir=both];
     "AMQP Servers" -> "designate-central Server 2" [dir=both];
     "AMQP Servers" -> "designate-central Server 3" [dir=both];
     "designate-central Server 1" -> "Database Servers";
     "designate-central Server 2" -> "Database Servers";
     "designate-central Server 3" -> "Database Servers";
   }

Notes
-----

You can run as many `designate-central` services as needed, as long as they all
have access to the AMQP server(s), work will be distributed across all of them.

designate-mdns
==============

Needs Access to:
----------------

* AMQP
* Database
* DNS Servers

.. graphviz::

   digraph MDNSHA {
     rankdir=LR
     {"AMQP Servers" [shape=box]
      "designate-mdns Server 1" [shape=box]
      "designate-mdns Server 2" [shape=box]
      "designate-mdns Server 3" [shape=box]
      "DNS Servers" [shape=egg]
      "Database Servers" [shape=cylinder]
     }
     subgraph "designate-mdns Servers" {
       cluster=true;
       label="designate-mdns Servers";
       "designate-mdns Server 1";
       "designate-mdns Server 2";
       "designate-mdns Server 3";
     }
     "AMQP Servers" -> "designate-mdns Server 1" [dir=both];
     "AMQP Servers" -> "designate-mdns Server 2" [dir=both];
     "AMQP Servers" -> "designate-mdns Server 3" [dir=both];
     "designate-mdns Server 1" -> "Database Servers" [dir=back];
     "designate-mdns Server 2" -> "Database Servers" [dir=back];
     "designate-mdns Server 3" -> "Database Servers" [dir=back];
     "designate-mdns Server 1" -> "DNS Servers"
     "designate-mdns Server 2" -> "DNS Servers"
     "designate-mdns Server 3" -> "DNS Servers"
   }

Notes
-----

You can run as many `designate-mdns` services as needed, as long as they all
have access to the AMQP server(s), work will be distributed across all of them.

designate-worker
================

Needs Access to:
----------------

* AMQP
* DNS Servers

.. graphviz::

   digraph WORKERSHA {
     rankdir=LR
     {"AMQP Servers" [shape=box]
      "designate-worker Server 1" [shape=box]
      "designate-worker Server 2" [shape=box]
      "designate-worker Server 3" [shape=box]
      "DNS Servers" [shape=egg]
     }
     subgraph "designate-worker Servers" {
       cluster=true;
       label="designate-worker Servers";
       "designate-worker Server 1";
       "designate-worker Server 2";
       "designate-worker Server 3";
     }
     "AMQP Servers" -> "designate-worker Server 1" [dir=both];
     "AMQP Servers" -> "designate-worker Server 2" [dir=both];
     "AMQP Servers" -> "designate-worker Server 3" [dir=both];
     "designate-worker Server 1" -> "DNS Servers"
     "designate-worker Server 2" -> "DNS Servers"
     "designate-worker Server 3" -> "DNS Servers"
   }

Notes
-----

You can run as many `designate-worker` services as needed, as long as they all
have access to the AMQP server(s), work will be distributed across all of them.

designate-producer
==================

Needs Access to:
----------------

* AMQP
* DLM

.. graphviz::

   digraph PRODUCERSHA {
     rankdir=LR
     {"AMQP Servers" [shape=box]
      "designate-producer Server 1" [shape=box]
      "designate-producer Server 2" [shape=box]
      "designate-producer Server 3" [shape=box]
      "DLM Servers" [shape=octagon]
     }
     subgraph "designate-producer Servers" {
       cluster=true;
       label="designate-producer Servers";
       "designate-producer Server 1";
       "designate-producer Server 2";
       "designate-producer Server 3";
     }
     "AMQP Servers" -> "designate-producer Server 1" [dir=both];
     "AMQP Servers" -> "designate-producer Server 2" [dir=both];
     "AMQP Servers" -> "designate-producer Server 3" [dir=both];
     "designate-producer Server 1" -> "DLM Servers"
     "designate-producer Server 2" -> "DLM Servers"
     "designate-producer Server 3" -> "DLM Servers"
   }

Notes
-----

You can run as many `designate-producer` services as needed, as long as they
all have access to the AMQP server(s), and a distributed lock manager,
work will be sharded across all the services.

You will need to set a coordination `backend_url`. This needs to be a DLM
that is supported by tooz, that supports group membership.
See `tooz driver list`_ for available drivers

.. warning:: Failure to set a `backend_url` can cause unexpected consequences, and may result in some periodic tasks being ran more than once.

.. code-block:: ini

   [coordination]
   backend_url = kazoo://<zookeeper url>:<zookeeper port>

designate-sink
==============

Needs Access to:
----------------

* AMQP

.. graphviz::

   digraph SINKSHA {
     rankdir=LR
     {"AMQP Servers" [shape=box]
      "designate-sink Server 1" [shape=box]
      "designate-sink Server 2" [shape=box]
      "designate-sink Server 3" [shape=box]
     }
     subgraph "designate-sink Servers" {
       cluster=true;
       label="designate-sink Servers";
       "designate-sink Server 1";
       "designate-sink Server 2";
       "designate-sink Server 3";
     }
     "AMQP Servers" -> "designate-sink Server 1" [dir=both];
     "AMQP Servers" -> "designate-sink Server 2" [dir=both];
     "AMQP Servers" -> "designate-sink Server 3" [dir=both];
   }

Notes
-----

You can run as many `designate-sink` services as needed, as long as they all
have access to the AMQP server(s), work will be distributed across all of them.


.. _tooz driver list: https://docs.openstack.org/tooz/latest/user/compatibility.html#grouping
