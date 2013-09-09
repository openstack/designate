..
    Copyright 2013 Hewlett-Packard Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

BIND9 Backend
=============

.. note::
   The BIND9 backend, while functional, is lacking a solid process for
   distributing zonefiles among multiple DNS servers. The soon to be introduced
   concept of "Pools" will provide a foundation to fix this.

Designate Configuration
-----------------------

Configuration Options required for BIND9 operation::

    [service:central]
    state-path = /var/lib/designate
    backend_driver = bind9

    [backend:bind9]
    rndc-host = 127.0.0.1
    rndc-port = 953
    rndc-config-file = /etc/bind9/rndc.conf  # If required by BIND9
    rndc-key-file = /etc/bind/rndc.key

BIND9 Configuration
-------------------

Include the Designate generated configuration in /etc/bind/named.conf.local::

    include "/var/lib/designate/bind9/zones.config";

Ensure BIND9 can access the above config, one way to achieve this is by
disabling AppArmour::

    $ touch /etc/apparmor.d/disable/usr.sbin.named
    $ service apparmor reload
    $ service bind9 restart

To ensure rndc addzone/delzone functionality edit named.conf.options, or
named.conf and add this line under options::

    allow-new-zones yes;
