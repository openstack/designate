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

.. _configpools:

==========================
Configuring Multiple Pools
==========================

Administrators can group DNS namespace servers into multiple pools to help
them manage their DNS environments. See :ref:`pools` to learn more about what
pools are and how you can use them.

Configuring Designate to use multiple pools consists of:

#. Defining new pools and loading their definitions into the database.

#. Configuring the pool scheduler with filters that you have created or with
   filters provided by Designate.

#. Supplying the required pool information to users to specify when they
   create zones.

Defining New Pools
==================

In Designate, you define a new pool in a pool definition file, and then load
the definition into the Designate database by running the ``designate-manage``
command.

#. Add the pool to the pool definition file, by following the required key
   value pairs in YAML format that are documented under "Pool Definition File"
   in :ref:`pools`.

   Here is an example of a pool definition file, ``pools.yaml``, that
   configures two different pools. Each pool supports a different usage level,
   `gold` and `standard`, and each contains zones that reflect their
   respective usage levels.

   The `gold` level provides 6 nameservers that users have access to. The
   `standard` level provides only 2 nameservers. Both pools have one target
   that is written to.

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


#. Load the definitions into the Designate database using the
   ``designate-manage pool update`` command:

   .. code-block:: bash

      # Do a dry run
      $ designate-manage pool update --file pools.yaml --dry-run
      $ designate-manage pool update --file pools.yaml

   Designate now has two pools to work with. The next step is to configure the
   pool scheduler to use the attributes--provided through filters--when
   choosing the pool to store the zone on.

Showing the configured pools
============================

In Designate, you can show the current configured default pool by running the
``designate-manage pool show_config`` command.
You can either see a different pool by adding --pool_id <POOL_ID>, or you can
see all the configured pools by adding ``--all_pools`` or just ``--all``.

Configuring TSIG Keys for Non-Default Pools
============================================

.. important::

   Non-default pools require TSIG (Transaction Signature) keys for zone
   transfers to function correctly. Without TSIG keys, zones in non-default
   pools will fail to synchronize with backend nameservers.

Why TSIG Keys Are Required
---------------------------

When backend nameservers request zone transfers via AXFR from Designate's
MiniDNS service, MDNS needs to identify which pool the requested zone belongs
to. MDNS uses TSIG authentication to make this determination:

* **With TSIG**: MDNS uses the TSIG key's resource_id to identify the pool
  and retrieve the correct zone.
* **Without TSIG**: MDNS defaults to searching only in the default pool,
  causing zones in other pools to fail with "ZoneNotFound" errors.

Creating and Configuring TSIG Keys
-----------------------------------

The process involves generating the TSIG key, configuring it in backend
nameservers, and registering it in Designate's database. MiniDNS reads
TSIG keys directly from the Designate database, so no separate MDNS
configuration is needed.

#. Generate a TSIG key using ``tsig-keygen``:

   .. code-block:: bash

      sudo tsig-keygen -a hmac-sha256 <key-name> > <path-to-key-file>

   This creates a file with content similar to:

   .. code-block:: text

      key "<key-name>" {
              algorithm hmac-sha256;
              secret "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";
      };

#. Configure the TSIG key in your backend nameservers. For BIND9, include
   the key in ``named.conf`` and configure it for use with MDNS:

   .. code-block:: text

      include "<path-to-key-file>";

      server <mdns-ip-address> {
        keys { <key-name>; };
      };

#. Create the TSIG key in Designate's database using the API:

   .. code-block:: bash

      # Extract the secret from the key file
      SECRET=$(grep secret <path-to-key-file> | awk '{print $2}' | tr -d '";')

      # Create the TSIG key in Designate for your pool
      openstack tsigkey create \
        --name <key-name> \
        --algorithm hmac-sha256 \
        --secret "$SECRET" \
        --scope POOL \
        --resource-id <pool-uuid>

#. Verify the TSIG key is properly configured:

   .. code-block:: bash

      # List TSIG keys
      openstack tsigkey list

      # Verify zones can now be created in the non-default pool
      openstack zone create --email admin@example.com \
        --attributes pool_id:<pool-uuid> \
        example.com.

Without completing all these steps, zones created in non-default pools will
remain in ERROR status, unable to synchronize with backend nameservers.

Configuring the Pool Scheduler
==============================

When a user creates a zone, the pool scheduler uses filters to assign the zone
to a particular DNS server pool. As the administrator, you choose an ordered
list of filters that runs on each ``zone create`` API request. You configure
the scheduler to use filters that are provided with Designate or create
your own.

#. Do one of the following:

   - Write one or more custom filters.

     See :ref:`poolsched`.

   - Choose one or more of the filters that Designate provides:

     - ``attribute``--assigns the zone to the pool whose attribute is
       specified.

     - ``pool_id_attribute``--if the user is a member of the specified role
       assigns the zone to the pool whose ID is specified.

     - ``default_pool``--assigns the zone to the default pool specified in the
       Designate configuration file.

     - ``fallback``--if there are no pools available, assigns the zone to the
       default pool.

     - ``random``--if multiple pools have been specified, randomly assigns the
       zone to a pool.

     - ``in_doubt_default_pool``--if none of the specified pools are
       available, and the default pool has not been specified, assigns the
       zone to the default pool.

#. Add the filters that you want the scheduler to use in the
   ``service:central`` section of the ``designate.conf`` file. See
   :ref:`poolsched` for more information.


Schedule by Pool ID Example
---------------------------

For example, to allow a user to select a pool by specifying an ID or
fallback to using a default, you could use the following configuration:

.. code-block:: ini

   [service:central]
   default_pool_id = 794ccc2c-d751-44fe-b57f-8894c9f5c842
   scheduler_filters = pool_id_attribute, fallback

The pool scheduler applies filters from left to right. If the zone body
doesn't contain an `attributes` object with a `pool_id` set to a valid pool
ID, the fallback filter is then called, returning the default pool as the
scheduled pool for that zone.


Schedule by Tier Example
------------------------

In this tier example, the `attribute` filter is used to select the
correct pool.

.. code-block:: ini

   [service:central]
   default_pool_id = 794ccc2c-d751-44fe-b57f-8894c9f5c842  # the std pool
   scheduler_filters = attribute, fallback

When a user wants to assign a zone to the `gold` pool, the user must provide
the appropriate attribute in the zone.

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

In this example, the user defines which pool is scheduled. If the zone should
be scheduled based on the tenant, a custom filter could be written that looks
up the appropriate group and adds the appropriate pool.
