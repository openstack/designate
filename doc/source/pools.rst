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

=====
Pools
=====

Contents:

.. toctree::
   :maxdepth: 2
   :glob:

   pools/scheduler


Overview
========

In designate we support the concept of multiple "pools" of DNS Servers.

This allows operators to scale out their DNS Service by adding more pools, avoiding
the scalling problems that some DNS servers have for number of zones, and the total
number of records hosted by a single server.

This also allows providers to have tiers of service (i.e. the difference
between GOLD vs SILVER tiers may be the number of DNS Servers, and how they
are distributed around the world.)

In a private cloud situation, it allows operators to separate internal and
external facing zones.

To help users create zones on the  correct pool we have a "scheduler" that is
responsible for examining the zone being created and the pools that are
availible for use, and matching the zone to a pool.

The filters are plugable (i.e. operator replaceable) and all follow a simple
interface.

The zones are matched using "zone attributes" and "pool attributes". These are
key: value pairs that are attached to the zone when it is being created, and
the pool. The pool attributes can be updated by the operator in the future,
but it will **not** trigger zones to be moved from one pool to another.

.. note::

    Currently the only zone attribute that is accepted is the `pool_id` attribute.
    As more filters are merged there will be support for dynamic filters.


Managing Pools
==============

In mitaka we moved the method of updating pools to a CLI in `designate-manage`

There is a YAML file that defines the pool, and is used to load this information into the database.


.. literalinclude:: ../../etc/designate/pools.yaml.sample
       :language: yaml

Designate Manage Pools Command Reference
----------------------------------------

Update Pools Information
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  designate-manage pool update [options]

Options:
""""""""

  --file        Input file (Default: ``/etc/designate/pools.yaml``)
  --dry_run     Simulate an update. (Default: False)
  --delete      Delete Pools that are not in the input file (Defaults: False)

.. warning::

  | Running with ``--delete True`` can be **extremely** dangerous.
  | It will delete any pools that are not in the supplied YAML file, and any
  | zones that are in that Pool.
  | Before running with ``--delete True`` we recommend operators run with
  | ``--delete True --dry_run True`` to view the outcome.



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
