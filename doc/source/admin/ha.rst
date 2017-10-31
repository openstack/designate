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

.. blockdiag::

   blockdiag {

      loadbalancer [label="L7 Load Balancer", stacked];
      amqp_servers [label="AMQP Servers", stacked]
      group api_servers {
        label = "API Servers";
        api_server_1 [label="API Server 1"];
        api_server_2 [label="API Server 2"];
        api_server_3 [label="API Server 3"];
      }
      loadbalancer -> api_server_1, api_server_2, api_server_3;
      api_server_1, api_server_2, api_server_3 -> amqp_servers;
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

.. blockdiag::

   blockdiag {

      amqp_servers [label="AMQP Servers", stacked]
      db_servers [label="Database Servers", stacked, shape=flowchart.database]
      group designate_central_servers {
        label = "designate-central Servers";
        designate_central_server_1 [label="designate-central Server 1", width=256];
        designate_central_server_2 [label="designate-central Server 2", width=256];
        designate_central_server_3 [label="designate-central Server 3", width=256];
      }
      amqp_servers <-> designate_central_server_1, designate_central_server_2, designate_central_server_3;
      designate_central_server_1, designate_central_server_2, designate_central_server_3 -> db_servers;
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

.. blockdiag::

   blockdiag {

      amqp_servers [label="AMQP Servers", stacked]
      dns_servers [label="DNS Servers", stacked, shape="cloud"]
      db_servers [label="Database Servers", stacked, shape=flowchart.database]
      group designate_mdns_servers {
        label = "designate-mdns Servers";
        designate_mdns_server_1 [label="designate-mdns Server 1", width=256];
        designate_mdns_server_2 [label="designate-mdns Server 2", width=256];
        designate_mdns_server_3 [label="designate-mdns Server 3", width=256];
      }
      amqp_servers <-> designate_mdns_server_1, designate_mdns_server_2, designate_mdns_server_3;
      designate_mdns_server_1, designate_mdns_server_2, designate_mdns_server_3 <- db_servers;
      designate_mdns_server_1, designate_mdns_server_2, designate_mdns_server_3 -> dns_servers;
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

.. blockdiag::

   blockdiag {

      amqp_servers [label="AMQP Servers", stacked]
      dns_servers [label="DNS Servers", stacked, shape="cloud"]
      group designate_worker_servers {
        label = "designate-worker Servers";
        designate_worker_server_1 [label="designate-worker Server 1", width=256];
        designate_worker_server_2 [label="designate-worker Server 2", width=256];
        designate_worker_server_3 [label="designate-worker Server 3", width=256];
      }
      amqp_servers <-> designate_worker_server_1, designate_worker_server_2, designate_worker_server_3;
      designate_worker_server_1, designate_worker_server_2, designate_worker_server_3 -> dns_servers;
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

.. blockdiag::

   blockdiag {

      amqp_servers [label="AMQP Servers", stacked]
      dlm_servers [label="DLM Servers", stacked]
      group designate_producer_servers {
        label = "designate-producer Servers";
        designate_producer_server_1 [label="designate-producer Server 1", width=256];
        designate_producer_server_2 [label="designate-producer Server 2", width=256];
        designate_producer_server_3 [label="designate-producer Server 3", width=256];
      }
      amqp_servers <-> designate_producer_server_1, designate_producer_server_2, designate_producer_server_3;
      designate_producer_server_1, designate_producer_server_2, designate_producer_server_3 -> dlm_servers;
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

.. blockdiag::

   blockdiag {

      amqp_servers [label="AMQP Servers", stacked]
      group designate_sink_servers {
        label = "designate-sink Servers";
        designate_sink_server_1 [label="designate-sink Server 1", width=256];
        designate_sink_server_2 [label="designate-sink Server 2", width=256];
        designate_sink_server_3 [label="designate-sink Server 3", width=256];
      }
      amqp_servers <-> designate_sink_server_1, designate_sink_server_2, designate_sink_server_3;
   }

Notes
-----

You can run as many `designate-sink` services as needed, as long as they all
have access to the AMQP server(s), work will be distributed across all of them.


.. _tooz driver list: https://docs.openstack.org/tooz/latest/user/compatibility.html#grouping
