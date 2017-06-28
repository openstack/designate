..
    Copyright 2015 Hewlett-Packard Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

***************************
Upgrading to Kilo from Juno
***************************

.. note::
   This doc section is a work in progress, for now, we have some smaller
   hints and tips for watchout for during the upgrade.

Tips and Tricks
===============

1. Two new Designate services

Two new Designate services were added in Kilo, designate-pool-manager and
designate-mdns. Please ensure to configure and enable these services as
part of the upgrade.


2. Post-Migration, existing DNS domains hosted by PowerDNS must have their
"masters" column manually populated with the list of designate-mdns ip and
port pairs, and their type switched to SECONDARY. For example:

.. code-block:: ruby

   UPDATE powerdns.domains SET type = "SECONDARY", masters = "192.0.2.1:5354,192.0.2.2:5354" WHERE masters IS NULL;
