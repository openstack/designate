..
    Copyright 2017 Rackspace, Inc.

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
Upgrading to Newton from Mitaka
===============================

The Newton release of Designate adds two new services ``designate-producer``,
``designate-worker``. These replace ``designate-zone-manager`` and
``designate-pool-manager``, respectively. In a future cycle, the old services
will be removed, and the new ones will be enabled by default. In Newton,
you must enable the new services yourself. Designate will work with both
configurations, as there is no breaking change from Mitaka.

Breaking Changes
----------------

The default port the ``designate-agent`` service listens on has changed
from 53 to 5358. This matches the port we have always used in the sample
configuration, and the port used in the agent backend class.

Upgrading Code and Enabling Services
------------------------------------

To enable the new services with minimal impact, the following process can
be followed. This assumes you have all Mitaka Designate services running.

1. Deploy the Newton code.
2. Add the ``[service:worker]`` and ``[service:producer]`` sections to your
   configuration file. Ensure ``enabled`` and ``notify`` in the worker section
   are ``True``.

    .. code-block:: ini

        [service:worker]
        enabled = True
        #workers = None
        #threads = 1000
        #threshold_percentage = 100
        #poll_timeout = 30
        #poll_retry_interval = 15
        #poll_max_retries = 10
        #poll_delay = 5
        notify = True

        [service:producer]
        #workers = None
        #threads = 1000
        # Can be any/all of: periodic_exists, delayed_notify, worker_periodic_recovery
        # None => All tasks enabled
        #enabled_tasks = None

        [producer_task:domain_purge]
        #interval = 3600  # 1h
        #batch_size = 100
        #time_threshold = 604800  # 7 days

        [producer_task:delayed_notify]
        #interval = 5

        [producer_task:worker_periodic_recovery]
        #interval = 120

3. Stop the ``designate-pool-manager`` and
   ``designate-zone-manager`` processes.
4. Restart the ``designate-api``, ``designate-central`` and
   ``designate-mdns`` services.
5. Start the ``designate-producer`` and ``designate-worker`` services.


New Features
------------

- ``designate-mdns``, ``designate-agent`` and ``designate-api`` can now bind to
  multiple host:port pairs via the new "listen" configuration arguments for
  each service.
- New pool scheduler  "attribute" filter for scheduling zones across pools.
  This can be enabled in the ``[service:central]`` section of the config by
  adding ``attribute`` to the list of values in the ``filters`` option.
- An experimental agent backend to support TinyDNS, the DNS resolver from the
  djbdns tools.
- An experimental agent backend to support Knot DNS 2
- A new recordset api ``/v2/recordsets`` is exposed, docs can be found
  `here <https://docs.openstack.org/api-ref/dns/#list-all-recordsets-owned-by-project>`_.
- Designate services now report running status. The information is exposed via
  `api <https://docs.openstack.org/api-ref/dns/#service-statuses>`_.
- The quotas API from the admin API has been ported to /v2 with some changes
  and is now `stable <https://docs.openstack.org/api-ref/dns/#quotas>`_.

Deprecation Notices
-------------------

- ``designate-api``'s api_host and api_port configuration options have been
  deprecated, please use the new combined "listen" argument in place of these.
- ``designate-mdns``'s host and port configuration options have been
  deprecated, please use the new combined "listen" argument in place of these.
- ``designate-agents``'s host and port configuration options have been
  deprecated, please use the new combined "listen" argument in place of these.
- ``designate-zone-manager`` and ``designate-pool-manager`` are now deprecated
  and will be removed in a future release.

