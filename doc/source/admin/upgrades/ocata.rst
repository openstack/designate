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

==============================
Upgrading to Ocata from Newton
==============================

Upgrading Code and Enabling Services
------------------------------------

1. Deploy Ocata code or packages.
2. Restart all services. See the Newton upgrade guide for enabling
   ``designate-producer`` and ``designate-worker``.

New Features
------------

- The notifications Designate emits via MQ are now pluggable, drivers are
  defined by python entrypoints and the new ``notification_plugin`` option
  in the ``DEFAULT`` config section enables selection. By default, the
  notifications have not changed. There is an ``audit`` plugin that can
  be used, if desired.

- Scheduling zones across pools. See :doc:`/admin/pool-scheduler`
  for more details.

Deprecation Notices
-------------------

- ``designate-zone-manager`` and ``designate-pool-manager`` remain deprecated
  and will be removed in a future release.
