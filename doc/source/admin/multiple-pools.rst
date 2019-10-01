..
    Copyright 2016 Rackspace Hosting

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


===============================
How To Configure Multiple Pools
===============================

Designate supports "pools" of nameservers. A pool is a collection of
nameservers and targets that Designate will write to and read from to
confirm changes are successful. In some cases you might have multiple
pools that you need to manage differently. For example, you might use
separate pools to distribute tenants across some subset of your DNS
infrastructure.

Read the section on :ref:`pools` to learn more about what pools are
and what they can do.

Pools Configuration
===================

Pools are configured by a `pools.yml` file. This file describes the
pools and can be used to update Designate via `designate-manage`
commands.

Here is an example `pools.yml` that configures two different
pools. The idea is that we'll configure our pools to support different
usage levels. We'll define a `gold` and `standard` level and put zones
in each based on the tenant.

Our `gold` level will provide 6 nameservers that users have access to
where our `standard` will only provide 2. Both pools will have one
master target we write to.

.. code-block:: yaml

   ---

   - name: golden_pool
     description: The golden pool!

     attributes:
       service_tier: gold

     ns_records:
       - hostname: ns1-gold.example.org
         priority: 1

       - hostname: ns2-gold.example.org
         priority: 2

       - hostname: ns3-gold.example.net
         priority: 3

       - hostname: ns4-gold.example.net
         priority: 4

       - hostname: ns5-gold.example.net
         priority: 5

       - hostname: ns6-gold.example.net
         priority: 6

     nameservers:
       - host: ns1-gold.example.net
         port: 53

       - host: ns2-gold.example.net
         port: 53

       - host: ns3-gold.example.net
         port: 53

       - host: ns4-gold.example.net
         port: 53

       - host: ns5-gold.example.net
         port: 53

       - host: ns6-gold.example.net
         port: 53

     targets:
       - type: bind9
         description: bind9 golden master

         masters:
           - host: mdns.designate.example.com
             port: 5354

         options:
           host: ns-master-gold.example.org
           port: 53
           rndc_host: ns-master-gold.example.org
           rndc_port: 953
           rndc_key_file: /etc/designate.rndc.key


   - name: standard_pool
     description: The standard pool

     attributes:
       service_tier: standard

     ns_records:
       - hostname: ns1-std.example.org
         priority: 1

       - hostname: ns2-std.example.org
         priority: 2

     nameservers:
       - host: ns1-std.example.net
         port: 53

       - host: ns2-std.example.net
         port: 53

     targets:
       - type: bind9
         description: bind9 golden master

         masters:
           - host: mdns.designate.example.com
             port: 5354

         options:
           host: ns-master-std.example.org
           port: 53
           rndc_host: ns-master-std.example.org
           rndc_port: 953
           rndc_key_file: /etc/designate.rndc.key


With our configuration in place, we can then update Designate to use
the pool configuration.

.. code-block:: bash

   # Do a dry run
   $ designate-manage pool update --file pools.yml --dry-run
   $ designate-manage pool update --file pools.yml

Designate now has two pools to work with. The next step will be to
configure the scheduler to use the attributes when choosing what pool
to store the zone on.


Pool Scheduler
==============

The pool scheduler allows selecting a pool when a zone is
created. Each scheduler acts as a filter, selecting or negating each
pool based on some attributes. Designate comes with some simple
schedulers to support common patterns:

 - default_pool
 - fallback
 - random
 - pool_id_attribute
 - attribute

These are configured in the `service:central` section of the
config.


Schedule by Pool ID Example
---------------------------

For example, if we wanted to allow a user to select a specific pool by
id or fallback to using a default, we could use the following
configuration.

.. code-block:: ini

   [service:central]
   default_pool_id = 794ccc2c-d751-44fe-b57f-8894c9f5c842
   scheduler_filters = pool_id_attribute, fallback

The filters are applied from left to right. If the zone body doesn't
contain an `attributes` object with a `pool_id` set to a valid pool
id, the fallback filter is then called, returning the default pool as
the scheduled pool for that zone.


Schedule by Tier Example
------------------------

In our tiered example, we'll use the `attribute` filter to select the
correct pool.

.. code-block:: ini

   [service:central]
   default_pool_id = 794ccc2c-d751-44fe-b57f-8894c9f5c842  # the std pool
   scheduler_filters = attribute, fallback

When a user needs the zone to go to the `gold` pool, the user needs to
provide the appropriate attribute in the zone.

.. code-block:: http

   POST /v2/zones HTTP/1.1
   Accept: application/json
   Content-Type: application/json

   {
       "attributes": {
           "service_tier": "gold"
       },
       "email": "user@example.com",
       "name": "example.net."
   }


This ensures the zone ends up on the correct pool.

In this example, we've allowed the user to define what pool should be
scheduled. If we wanted to schedule the zone based on the tenant, we
could write a custom filter that looked up the appropriate group and
adds the appropriate pool.
