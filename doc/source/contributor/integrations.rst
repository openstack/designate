:orphan:

..
    Copyright 2013 Rackspace Hosting

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

======================
OpenStack Integrations
======================

This page overviews integrations with other services like Neutron and others to
make use of Designate more convenient.

Reverse - FloatingIP
====================

The FloatingIP PTR feature of Designate relies on information of the FloatingIP
which is in a different service than Designate itself. It can be in any service
as long as there is a "plugin" for it that can be loaded via the configuration
setting called "network_api".

* Controller, views and schemas in the V2 API
* RPC Client towards Central used by the API and Sink
* Logic in Central to make it convenient for setting, unsetting, listing and
  getting FloatingIP PTR records compared to the Records themselves which would
  be more work. (This is outlined in code docstrings for the specific methods.)
* Sink handlers for the various backend to help us be more consistent.

Record invalidation
^^^^^^^^^^^^^^^^^^^
Happens mainly happens via comparing a Tenant's FloatingIPs
towards the list we have of Records which are of a certain plugin type and
with the use of a Sink handler that listens for incoming events from the
various services.

Configuring Neutron
-------------------

Configuring the FloatingIP feature is really simple:

.. code-block:: ini

    [network_api:neutron]
    endpoints = RegionOne|http://localhost:9696
    endpoint_type = publicURL
    timeout = 30
    insecure = False
    ca_certificates_file = /etc/path/to/ca.pem

Note that using admin_user, admin_password and admin_tenant_name is optional,
if not present we'll piggyback on the context.auth_token passed in by the API.

.. note::
    If "endpoints" is not configured and there's no service catalog is present
    in the context passed by the API to Central the request will fail in
    a NoEndpoint exception.

Neutron Designate direct integration
====================================

Neutron supports creating DNS Recordsets as neutron ports are created, and
pushing that information into designate.

The configuration for this is in the `Networking Guide <https://docs.openstack.org/neutron/latest/admin/config-dns-int.html>`_

Designate Sink
==============

:ref:`designate-sink` is a component of designate that can listen to the event
stream of other openstack services and perform actions based on them.


