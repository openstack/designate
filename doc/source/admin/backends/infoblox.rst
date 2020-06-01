..
    Copyright 2015 Infoblox, Inc.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Infoblox Backend
================

Provides an integration between Designate and Infoblox grids.

Features
--------

The Infoblox Designate backend allows an Infoblox grid to be used for
serving zones controlled by OpenStack Designate.

The Infoblox backend may be setup to map a specific Designate pool to
a single DNS view, or it may be setup to map individual tenants to
per-tenant DNS views.

Infoblox Configuration
----------------------

* Create a user for use by Designate.
* Set up one or more nameserver groups to be used to serve Designate zones.

  * Set the Designate mDNS servers as external primaries
  * Add a grid member as a grid secondary; select the "Lead Secondary" option
    for this member
  * Add additional grid secondaries as desired

Designate Backend Configuration
-------------------------------

* Designate may be configured to talk to any number of grid API service points
  (GM or Cloud appliance).

  * Setup a pool for each combination of DNS view and nameserver group you wish
    to manage.
  * Setup a pool target for each API service point that Designate should talk
    to.

    * A single Designate pool should point to only one API service point in any
      single grid. That is, do not point a pool at more than one API service
      point in the same grid.
    * It is OK to point a pool at multiple grids, just not to multiple service
      points on the same grid.
    * You may specify the DNS view and nameserver group on a per-target basis.


* The ``[infoblox:backend]`` stanza in the designate configuration file can be
  used to set default values for the grid connectivity and other information.
* These values can be overridden on a per-target basis with the "options"
  element of the target configuration.
* Set the mDNS port to 53 in the ``[service:mdns]`` stanza.
* Designate always puts any servers associated with the pool as NS records for
  the domain. So, if you wish for any Infoblox nameservers to be listed in NS
  records, they must be added via Designate.

Multi-tenant Configuration
--------------------------

When configured with ``multi_tenant = True`` in the designate.conf file, the
DNS view will be chosen as follows:

* A search will be made for a network view with the EA "TenantID", with the
  value of the OpenStack tenant_id.
* If found, then DNS view used will be <dns_view>.<network_view>, where
  <dns_view> is the value specified in designate.conf, and <network_view> is
  the name of the view found in the search.
* If no such network view is found, then a network view will be created with
  the name <network_view>.<tenant_id>, where <network_view> is the value
  specified in designate.conf.
  This network view will be tagged with the TenantID EA.
* If the DNS view does not exist (in either case above), then it will be
  created.
