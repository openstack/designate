..
    Copyright (c) 2014 Rackspace Hosting
    All Rights Reserved.

    Author: Jordan Cazamias <jordan.cazamias@rackspace.com>

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

    enabled_extensions_admin = quotas

Once this line has been added, restart the designate-central and designate-api
services.

Get Quotas
----------

.. http:get:: /quotas/TENANT_ID

    Retrieves quotas for tenant with the specified TENANT_ID.  The
    following example retrieves the quotas for tenant 12345.

    **Example request:**

    .. sourcecode:: http

        GET /admin/quotas/12345 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 201 Created
        Content-Type: application/json

        {
          "quota": {
            "zones": 10,
            "recordset_records": 20,
            "zone_records": 500,
            "zone_recordsets": 500
          }
        }

    :form zones: Number of zones the tenant is allowed to own
    :form recordset_records: Number of records allowed per recordset
    :form zone_records: Number of records allowed per zone
    :form zone_recordsets: Number of recordsets allowed per zone

    :statuscode 200: Success
    :statuscode 401: Access Denied

Update Quotas
-------------

.. http:patch:: /quotas/TENANT_ID

    Updates the specified quota(s) to their new values.

    **Example request:**

    .. sourcecode:: http

        PATCH /admin/quotas/12345 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json

        {
          "quota": {
            "zones": 1000,
            "zone_records": 50
          }
        }


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "quota": {
            "zones": 1000,
            "recordset_records": 20,
            "zone_records": 50,
            "zone_recordsets": 500
          }
        }

    :statuscode 200: Success
    :statuscode 401: Access Denied

Reset Quotas to Default
-----------------------

.. http:delete:: /quotas/TENANT_ID

    Restores the tenant's quotas back to their default values.

    **Example request:**

    .. sourcecode:: http

        DELETE /admin/quotas/12345 HTTP/1.1
        Host: 127.0.0.1:9001
        Accept: application/json
        Content-Type: application/json


    **Example response:**

    .. sourcecode:: http

        HTTP/1.1 204 No Content

    :statuscode 204: No Content
    :statuscode 401: Access Denied

