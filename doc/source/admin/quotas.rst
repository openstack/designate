..
    Copyright 2016 Rackspace Inc.

    Author: Tim Simmons <tim.simmons@rackspace.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


View and Manage Quotas
======================

Quotas exist in Designate for various resources, these are configurable by an
operator globally, as well as on a per-tenant basis.

View Quotas
-----------

Users can view their quotas with a simple API call:

.. code-block:: http

  GET /v2/quotas/ HTTP/1.1
  Accept: application/json
  Content-Type: application/json

Response:

.. code-block:: http

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-bfcd0723-624c-4ec2-bbd5-99e985efe8db

  {
    "api_export_size": 1000,
    "recordset_records": 20,
    "zone_records": 500,
    "zone_recordsets": 500,
    "zones": 500
  }

Administrators with the ability to use the ``X-Auth-All-Projects`` header
can view the quotas of any user by making a similar API call to
``/v2/quotas/tenant``.

Available Quotas
----------------

Zones
^^^^^

+---------+---------------------------------------+---------+
| Quota   | Description                           | Default |
+---------+---------------------------------------+---------+
| zones   | The number of zone allowed per tenant | 10      |
+---------+---------------------------------------+---------+

Recordsets/Records
^^^^^^^^^^^^^^^^^^

+------------------+------------------------------------------+---------+
| Quota            | Description                              | Default |
+------------------+------------------------------------------+---------+
| zone_recordsets  | Number of recordsets allowed per zone    | 500     |
+------------------+------------------------------------------+---------+
| zone_records     | Number of records allowed per zone       | 500     |
+------------------+------------------------------------------+---------+
| recordset_records| Number of records allowed per recordset  | 20      |
+------------------+------------------------------------------+---------+


Zone Exports
^^^^^^^^^^^^

+-----------------+-------------------------------------------------+---------+
| Quota           | Description                                     | Default |
+-----------------+-------------------------------------------------+---------+
| api_export_size | Number of recordsets allowed in a zone export   | 1000    |
+-----------------+-------------------------------------------------+---------+


Editing Quotas
--------------

Global Configuration
^^^^^^^^^^^^^^^^^^^^

All of the quotas above can be set as a default for all users by editing the
``[DEFAULT]`` configuration section, and setting each quota with
``quota_$name``. for example::

    [DEFAULT]
    ########################
    ## General Configuration
    ########################
    quota_zones = 500
    quota_zone_recordsets = 500
    quota_zone_records = 500
    quota_recordset_records = 20
    quota_api_export_size = 1000

Per-Tenant via API
^^^^^^^^^^^^^^^^^^

These quotas can be edited via API on a per-tenant basis. An administrator
can edit quotas for any tenant, but they must supply the
``X-Auth-All-Projects`` header, and have permission to use it, they'll also
need the ``set-quotas`` permission in ``policy.json``. For example, an
admin setting the zones quota for tenant X would look like:

.. code-block:: http

  PATCH /v2/quotas/tenantX HTTP/1.1
  Accept: application/json
  Content-Type: application/json
  X-Auth-All-Projects: True

  {
    "zones": 100
  }

The response would be:

.. code-block:: http

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-bfcd0723-624c-4ec2-bbd5-99e985efe8db

  {
    "api_export_size": 1000,
    "recordset_records": 20,
    "zone_records": 500,
    "zone_recordsets": 500,
    "zones": 100
  }
