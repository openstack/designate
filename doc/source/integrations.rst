============
Integrations
============

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
    # This is optional - if these credentials are not provided designate will
    # use the users context and auth token to query neutron
    #admin_username = designate
    #admin_password = designate
    #admin_tenant_name = designate
    auth_url = http://localhost:35357/v2.0
    insecure = False
    auth_strategy = keystone
    ca_certificates_file = /etc/path/to/ca.pem

Note that using admin_user, admin_password and admin_tenant_name is optional,
if not present we'll piggyback on the context.auth_token passed in by the API.

.. note::
    If "endpoints" is not configured and there's no service catalog is present
    in the context passed by the API to Central the request will fail in
    a NoEndpoint exception.
