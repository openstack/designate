..
    Copyright 2016 Hewlett Packard Enterprise Development Company LP

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _pools:

================
DNS Server Pools
================

About Pools
===========

Administrators can group DNS namespace servers into multiple pools to help
them manage their DNS environments. You can provide users with tiers of
service, by configuring pools to offer more capacity and better geographical
proximity. Administrators of private clouds can leverage multiple pools to
separate internal and external facing zones.

By default, Designate contains only one DNS server pool called ``default``.
When users create a zone in a multi-pool environment, the pool scheduler must
select a pool to host the new zone. Administrators control pool selection
through the use of filters, that the scheduler uses to select a pool for the
new zone.

The filter interface consists of pool attributes that are key-value pairs that
the scheduler attaches to the zone during creation.
Administrators can update pool attributes later, but none of the updates will
trigger zones to move to another pool.
Zones can be moved manually to a different pool, as mentioned in the
`API Reference <https://docs.openstack.org/api-ref/dns/dns-api-v2-index.html#pool-move-zone>`_.

Designate provides a set of filters that reflect some common use cases and
also a simple interface that administrators can use to create custom filters.


Process Overview for Configuring Multiple Pools
===============================================

The process of configuring multiple DNS server pools in Designate, consists
of the following steps:

#. Define the new pool in the pool definition file.

#. Load the new pool definition into the Designate database by running the
   ``designate-manage`` command.

#. Configure the pool scheduler to use one or more filters to match any
   new zones that users create with the appropriate pool. You can choose
   filters that are provided with Designate, or create new filters.

#. Supply the required pool information to users to specify when they create
   zones.


Pool Definition File
====================

A pool definition file is required when you create a DNS server pool in
Designate. The required key value pairs in YAML format are documented here:

.. literalinclude:: ../../../etc/designate/pools.yaml.sample
       :language: yaml


.. _catalog_zones:

Pools.yaml attributes
---------------------

NS records
^^^^^^^^^^

The ns_records section is the list of name servers Designate will advertise in
the zones as available for query. Nameservers listed in the ns_records section
are expected to be advertised from external networks.

Nameservers
^^^^^^^^^^^

The nameservers section is the list of name servers Designate will query to
confirm an update has completed on all of the Designate managed nameservers.
Nameservers listed in the nameservers section are not expected to be advertised
from external networks unless they are also listed in the ns_records section.

NS Records vs. Nameservers: Understanding the Differences
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There isn't always a direct relationship between the ns_records and the
nameservers sections, as they serve different use cases. Here are a few use
cases:

* ns_records list is equal to the nameservers list:
    The end user may want to query all of the advertised nameservers to confirm
    that their updates have successfully propagated.
* ns_records list is smaller than the nameservers list:
    The end user may have some private, or stealth, nameservers that they do
    not want to advertise publicly as ns_records. Because they are private,
    these stealth nameservers are not expected be necessarily reachable from
    external networks.
* ns_records list is larger than the nameservers list:
    The end user may not want to query all of the nameservers they manage
    after a zone update as some of those nameservers might be backup, or
    maybe the list of nameservers is just too big to query all of them.

Targets
^^^^^^^

The targets section defines how Designate should communicate with the backend
nameservers and how those backend nameservers should communicate with MiniDNS.
For the BIND driver, the options section defines the address and port the
“NOTIFY” messages should go to and the IP:port the driver should use to make
rndc calls to BIND, as can be seen in
:ref:`this example. <bind9_target_example>`
PowerDNS require using the connection keyword, as can be seen above.

Catalog zones
^^^^^^^^^^^^^

Catalog zones provide easy provisioning capabilities of zones to secondary
nameservers, transferred via AXFR from a special zone, the *catalog zone*.

In Designate, catalog zones are configured per pool. A catalog zone will
include all zones from the pool (except the catalog zone itself), called
*member zones*. That means all zones from that pool are automatically
synced to secondary name servers upon zone creation, update or deletion.
For more details about catalog zones, see
`RFC 9432 <https://datatracker.ietf.org/doc/rfc9432/>`_.

Catalog zones can be configured in ``pools.yaml`` via the *catalog_zone* key
(see the sample above). This example instructs a PowerDNS server listening at
``192.0.2.2:53`` to pull zones via AXFR from Designate's ``mini-DNS`` at
``192.0.2.1:5354``. Note that the secondary nameserver also needs to be
properly configured to consume the catalog zone. Please refer to the secondary
nameserver's documentation for details. Once this is set up and applied using
``designate-manage pool update``, Designate will handle the catalog zone
creation as well as synchronization of member zones.

As secondary nameservers configure their zones based on zone transfers (AXFR)
from the catalog zone, it is highly recommended to use transaction signatures
(TSIG) for secure and authenticated zone transfers. See the above sample for
details on how to use catalog zones with TSIG.

.. warning::

  | Even though not mandatory, it is highly recommended to secure transfers of
  | catalog zones with TSIG.


designate-manage pool Command Reference
=======================================

You manage pools in Designate with the ``designate-manage pool`` commands.

.. note::

   Control plane does not need to be restarted after designate-manage pool command changes.

Pool update
-----------
You manage can modify the current deployed pools with the
``designate-manage pool update`` command.

.. code-block:: console

   designate-manage pool update [options]

Pool update options
^^^^^^^^^^^^^^^^^^^
``--file <file>``
  Input file. When a file is not specified, ``/etc/designate/pools.yaml`` is
  used by default.

``--dry-run``
  Simulates what happens when you run this command.

``--delete``
  Removes all pools not listed in the config file.


.. warning::

  Using ``--delete`` can be **extremely** dangerous, because ``designate-manage`` removes any pools that are not in the supplied YAML file, **including the default one** and any zones that are in those pools. Before using ``--delete``, use ``--delete --dry-run`` to view the outcome.

Generating a Copy of the Pool Configuration
-------------------------------------------

.. code-block:: console

   designate-manage pool generate_file [options]


Options
^^^^^^^

``--file <file>``
  The YAML file where ``designate-manage`` writes its output. When a file is
  not specified, ``designate-manage`` writes to ``/etc/designate/pools.yaml``.

Showing the current Pools Configuration
---------------------------------------

.. code-block:: console

   designate-manage pool show_config [options]


Options
^^^^^^^

``--pool_id <pool_id>``
  ID of the pool to be examined.

``--all_pools``
  Show the config of all the pools.
