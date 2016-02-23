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
* Set up one or more name server groups to be used to serve Designate zones.

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

*Example Designate Configuration*

.. code-block:: ini

 [pool:794ccc2c-d751-44fe-b57f-8894c9f5c842]
 #Specify the API service points for each grid
 targets = f26e0b32-736f-4f0a-831b-039a415c481e
 # Specify the lead secondary servers configured in the NS groups
 # for each target.
 nameservers = ffedb95e-edc1-11e4-9ae6-000c29db281b

 [pool_target:f26e0b32-736f-4f0a-831b-039a415c481e]
 type = infoblox
 # wapi_url, username, password can all be overridden from the defaults
 # allowing targets to point to different grids
 options = dns_view: default, ns_group: Designate

 [pool_nameserver:ffedb95e-edc1-11e4-9ae6-000c29db281b]
 host=172.16.98.200
 port=53

 [backend:infoblox]
 # The values below will be used for all targets unless overridden
 # in the target configuration. http_* options may only be set here,
 # not at the target level.
 http_pool_maxsize = 100
 http_pool_connections = 100
 wapi_url = https://172.16.98.200/wapi/v2.1/
 sslverify = False
 password = infoblox
 username = admin
 multi_tenant = False

Multi-tenant Configuration
--------------------------

When configured with ``multi_tenant = True`` in the designate.conf file, the
DNS view will be chosen as follows:

* A search will be made for a network view with the EA "TenantID", with the
  value of the OpenStack tenant_id.
* If found, then then DNS view used will be <dns_view>.<network_view>, where
  <dns_view> is the value specified in designate.conf, and <network_view> is
  the name of the view found in the search.
* If no such network view is found, then a network view will be created with the
  name <network_view>.<tenant_id>, where <network_view> is the value specified
  in designate.conf. This network view will be tagged with the TenantID EA.
* If the DNS view does not exist (in either case above), then it will be
  created.
