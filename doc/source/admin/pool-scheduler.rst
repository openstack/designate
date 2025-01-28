..
    Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _poolsched:

======================
Pool Scheduler Filters
======================

About Filters
=============

When a user creates a zone, the pool scheduler uses filters to assign the zone
to a particular DNS server pool. As the administrator, you choose an ordered
list of filters that runs on each ``zone create`` API request. You configure
the scheduler to use filters that are provided with Designate or create
your own.


Filters Provided with Designate
===============================

Designate provides several filters that represent common use cases.

Base Class - Filter
-------------------

.. autoclass:: designate.scheduler.filters.base.Filter
    :members:

Attribute Filter
----------------

.. autoclass:: designate.scheduler.filters.attribute_filter.AttributeFilter
    :members: name
    :show-inheritance:

Pool ID Attribute Filter
------------------------

.. autoclass:: designate.scheduler.filters.pool_id_attribute_filter.PoolIDAttributeFilter
    :members:
    :undoc-members:
    :show-inheritance:

Random Filter
-------------

.. autoclass:: designate.scheduler.filters.random_filter.RandomFilter
    :members: name
    :show-inheritance:

Fallback Filter
---------------

.. autoclass:: designate.scheduler.filters.fallback_filter.FallbackFilter
    :members: name
    :show-inheritance:


Default Pool Filter
-------------------

.. autoclass:: designate.scheduler.filters.default_pool_filter.DefaultPoolFilter
    :members: name
    :show-inheritance:

In Doubt Default Pool Filter
----------------------------

.. autoclass:: designate.scheduler.filters.in_doubt_default_pool_filter.InDoubtDefaultPoolFilter
    :members: name
    :show-inheritance:


Creating Custom Filters
=======================

You can create your own filters by extending
:class:`designate.scheduler.filters.base.Filter`
and registering a new entry point in the ``designate.scheduler.filters``
namespace in ``designate.conf``:

.. code-block:: ini

   [entry_points]
   designate.scheduler.filters =
   my_custom_filter = my_extension.filters.my_custom_filter:MyCustomFilter


Configuring Filters in the Scheduler
====================================

After you have decided whether to use the filters provided with Designate or
create custom filters you must configure the filters in the pool scheduler.

Inside the ``designate.conf`` file under the ``[service:central]`` section,
add the filters that you want the scheduler to use to the
``scheduler_filters`` parameter:

.. code-block:: ini

    [service:central]
    scheduler_filters = attribute, pool_id_attribute, fallback, random, my_custom_filter

.. important::
  The scheduler runs the filters list from left to right.
