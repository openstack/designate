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

Overview
========

In designate we support the concept of multiple "pools" of DNS Servers.

This allows operators to scale out their DNS Service by adding more pools,
avoiding the scaling problems that some DNS servers have for number of zones,
and the total number of records hosted by a single server.

This also allows providers to have tiers of service (i.e. the difference
between GOLD vs SILVER tiers may be the number of DNS Servers, and how they
are distributed around the world.)

In a private cloud situation, it allows operators to separate internal and
external facing zones.

To help users create zones on the  correct pool we have a "scheduler" that is
responsible for examining the zone being created and the pools that are
available for use, and matching the zone to a pool.

The filters are pluggable (i.e. operator replaceable) and all follow a simple
interface.

The zones are matched using "zone attributes" and "pool attributes". These are
key: value pairs that are attached to the zone when it is being created, and
the pool. The pool attributes can be updated by the operator in the future,
but it will **not** trigger zones to be moved from one pool to another.

.. note::

    Currently the only zone attribute that is accepted is the `pool_id` attribute.
    As more filters are merged there will be support for dynamic filters.

Target vs. Nameserver
=====================

One thing that can be confusing about pools is the differentiation
between a target and a nameserver. The target is where Designate will
try to write the change, while a namserver is where Designate checks
that the change exists.

A great example of this is `bind's stealth master system
<http://www.zytrax.com/books/dns/ch4/#stealth>`_. In this
configuration, there could be a stealth master that you configure as
your target and a set of slaves pointed to that master as your
nameservers. Designate will write to the master and then look for the
changes on the slaves before considering the change active.

Another example would be where Designate uses an API backend such as
DynDNS or even another Designate instance. In this situation, you will
typically have a single target with a set of nameservers to test that
meet your requirements.

Managing Pools
==============

In mitaka we moved the method of updating pools to a CLI in `designate-manage`

There is a YAML file that defines the pool, and is used to load
this information into the database.


.. literalinclude:: ../../../etc/designate/pools.yaml.sample
       :language: yaml

.. _catalog_zones:

Catalog zones
-------------

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


Designate Manage Pools Command Reference
----------------------------------------

Update Pools Information
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  designate-manage pool update [options]

Options:
""""""""

  --file        Input file (Default: ``/etc/designate/pools.yaml``)
  --dry-run     This will simulate what will happen when you run this command
  --delete      Any Pools not listed in the config file will be deleted

.. warning::

  | Running with ``--delete`` can be **extremely** dangerous.
  | It will delete any pools that are not in the supplied YAML file, and any
  | zones that are in that Pool.
  | Before running with ``--delete`` we recommend operators run with
  | ``--delete --dry-run`` to view the outcome.



Generate YAML File
^^^^^^^^^^^^^^^^^^

.. code-block:: console

    designate-manage pool generate_file [options]

Options:
""""""""

  --file        YAML file output too (Default: ``/etc/designate/pools.yaml``)

Generate YAML File from Liberty Config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    designate-manage pool export_from_config [options]

Options:
""""""""

  --file        YAML file output too (Default: ``/etc/designate/pools.yaml``)
