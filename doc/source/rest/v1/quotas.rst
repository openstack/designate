..
    Copyright 2014 Hewlett-Packard Development Company, L.P.

    Author: Endre Karlson <endre.karlson@hp.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Quotas
======

Overview
--------
The quotas extension can be used to retrieve a tenant's absolute limits.

*Note*: Quotas is an extension and needs to be enabled before it can be used.
If Designate returns a 404 error, ensure that the following line has been
added to the designate.conf file::

    enabled_extensions_v1 = quotas, ...

Once this line has been added, restart the designate-central and designate-api
services.

Get Quotas
----------

.. http:get:: /quotas/TENANT_ID

    Retrieves quotas for tenant with the specified TENANT_ID.  The
    following example retrieves the quotas for tenant 12345.

    **Example request:**

    .. sourcecode:: http

        GET /v1/quotas/12345 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
          "api_export_size": 1000,
          "domains": 10,
          "recordset_records": 20,
          "domain_records": 500,
          "domain_recordsets": 500
        }

    :from api_export_size: Number of recordsets allowed in a zone export
    :form domains: Number of domains the tenant is allowed to own
    :form recordset_records: Number of records allowed per recordset
    :form domain_records: Number of records allowed per domain
    :form domain_recordsets: Number of recordsets allowed per domain

    :statuscode 200: Success
    :statuscode 401: Access Denied

Update Quotas
-------------

.. http:put:: /quotas/TENANT_ID

    Updates the specified quota(s) to their new values.

    **Example request:**

    .. sourcecode:: http

        PUT /v1/quotas/12345 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
          "domains": 1000,
          "domain_records": 50
        }


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "api_export_size": 1000,
          "domains": 1000,
          "recordset_records": 20,
          "domain_records": 50,
          "domain_recordsets": 500
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

Reset Quotas to Default
-----------------------

.. http:delete:: /quotas/TENANT_ID

    Restores the tenant's quotas back to their default values.

    **Example request:**

    .. sourcecode:: http

        DELETE /v1/quotas/12345 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 Success

    :statuscode 200: Success
    :statuscode 401: Access Denied

