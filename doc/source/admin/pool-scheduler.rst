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

.. _pool_scheduler:

==============
Pool Scheduler
==============

In designate we have a pluggable scheduler filter interface.

You can set an ordered list of filters to run on each zone create api request.

We provide a few basic filters below, and creating custom filters follows a
similar pattern to schedulers.

You can create your own by extending
:class:`designate.scheduler.filters.base.Filter`
and registering a new entry point in the ``designate.scheduler.filters``
namespace like so in your ``setup.cfg`` file:

.. code-block:: ini

   [entry_points]
   designate.scheduler.filters =
   my_custom_filter = my_extension.filters.my_custom_filter:MyCustomFilter

The new filter can be added to the
``scheduler_filters`` list in the ``[service:central]`` section like so:

.. code-block:: ini

    [service:central]

    scheduler_filters = attribute, pool_id_attribute, fallback, random, my_custom_filter

The filters list is ran from left to right, so if the list is set to:

.. code-block:: ini

    [service:central]

    scheduler_filters = attribute, random

There will be two filters ran,
the :class:`designate.scheduler.filters.attribute_filter.AttributeFilter`
followed by :class:`designate.scheduler.filters.random_filter.RandomFilter`


Default Provided Filters
========================

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
