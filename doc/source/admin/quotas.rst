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

Quotas exist in Designate for various resources. You can configure quotas
globally or on a per-project basis.

Viewing Quotas
--------------

.. _Designate plugin: https://docs.openstack.org/python-designateclient/latest/user/shell-v2.html
.. _OpenStack Client: https://docs.openstack.org/python-openstackclient/latest/

The `Designate plugin`_ for the `OpenStack Client`_ allows users to query their
current quota using the ``dns quota list`` command.

.. code-block:: console

    $ openstack dns quota list
    +-------------------+-------+
    | Field             | Value |
    +-------------------+-------+
    | api_export_size   | 1000  |
    | recordset_records | 20    |
    | zone_records      | 500   |
    | zone_recordsets   | 500   |
    | zones             | 10    |
    +-------------------+-------+

Users can also view their quotas with a simple
`View Current Project's Quotas Designate API <https://docs.openstack.org/api-ref/dns/#view-current-project-s-quotas>`_ call:

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
    "zones": 10
  }

Administrators with a cross-project read role can query the quotas for other
projects using the ``--project-id`` option to the ``dns quota list`` command or by
specifying a project_id when making the
`View Quotas Designate API <https://docs.openstack.org/api-ref/dns/#view-quotas>`_ call.

.. code-block:: console

    $ openstack dns quota list --project-id ecd4341280d645e5959d32a4b7659da1
    +-------------------+-------+
    | Field             | Value |
    +-------------------+-------+
    | api_export_size   | 1000  |
    | recordset_records | 20    |
    | zone_records      | 500   |
    | zone_recordsets   | 500   |
    | zones             | 20    |
    +-------------------+-------+

.. code-block:: http

  GET /v2/quotas/ecd4341280d645e5959d32a4b7659da1 HTTP/1.1
  Accept: application/json
  Content-Type: application/json

Modifying Quotas
----------------

You can edit Designate quotas on a per-project basis. An administrator
can edit quotas for any project, but they must have an `all_tenants` role or
use a system scoped admin token.

Administrators can set a custom quota for a project using the
`OpenStack Client`_ ``dns quota set`` command.

.. code-block:: console

    $ openstack dns quota set --project-id ecd4341280d645e5959d32a4b7659da1 --zones 30
    +-------------------+-------+
    | Field             | Value |
    +-------------------+-------+
    | api_export_size   | 1000  |
    | recordset_records | 20    |
    | zone_records      | 500   |
    | zone_recordsets   | 500   |
    | zones             | 30    |
    +-------------------+-------+

Below is an example of setting a quota using the
`Set Quotas Designate API <https://docs.openstack.org/api-ref/dns/#set-quotas>`_.

.. code-block:: http

  PATCH /v2/quotas/ecd4341280d645e5959d32a4b7659da1 HTTP/1.1
  Accept: application/json
  Content-Type: application/json
  X-Auth-All-Projects: True

  {
    "zones": 30
  }

The response would be:

.. code-block:: http

  HTTP/1.1 200 OK
  Content-Type: application/json; charset=UTF-8
  X-Openstack-Request-Id: req-ee264c7d-d9f3-4de8-92ec-7de4dc93a255

  {
    "api_export_size": 1000,
    "recordset_records": 20,
    "zone_records": 500,
    "zone_recordsets": 500,
    "zones": 30
  }

Resetting Quotas
----------------

You can reset custom quotas for a project to their default values by using the
``dns quota reset`` command. Administrators can reset quotas for any project, but
they must have an `all_tenants` role or use a system scoped admin token.

.. code-block:: console

    $ openstack dns quota reset --project-id ecd4341280d645e5959d32a4b7659da1

.. note:: There is no output from a successful ``dns quota reset`` command.

Below is an example of resetting a project's quota via the
`Reset Quota Designate API <https://docs.openstack.org/api-ref/dns/#reset-quotas>`_.

.. code-block:: http

  DELETE /v2/quotas/ecd4341280d645e5959d32a4b7659da1 HTTP/1.1
  Accept: application/json
  Content-Type: application/json
  X-Auth-All-Projects: True

The response would be:

.. code-block:: http

  HTTP/1.1 204 No Content
  X-Openstack-Request-Id: req-82b85853-145d-4253-be86-b9aa3116b975

Available Quotas
----------------

The quotas available in Designate are listed below with a short description
and the default values.

Zones
^^^^^

+---------+----------------------------------------+---------+
| Quota   | Description                            | Default |
+---------+----------------------------------------+---------+
| zones   | The number of zone allowed per project | 10      |
+---------+----------------------------------------+---------+

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

Default Quotas
--------------

You can set a default value for each quota that applies to all users by editing
the ``[DEFAULT]`` configuration section of the ``designate.conf`` file, for
example::

    [DEFAULT]
    ########################
    ## General Configuration
    ########################
    quota_zones = 10
    quota_zone_recordsets = 500
    quota_zone_records = 500
    quota_recordset_records = 20
    quota_api_export_size = 1000

Project ID Verification
-----------------------

Although Designate API can accept arbitrary strings as the Project ID to set
the quota for, actual enforcement of quota will be performed only when the
project ID of the quota matches the ``project-id`` in the request that
attempts to create a resource.

To prevent mistakes when specifying the ``project-id`` for a quota, you can
turn on project ID verification in the Designate configuration file:

.. code-block:: ini

   [service:api]
   quotas_verify_project_id = True

You must also specify how Designate connects to Keystone and locates the
appropriate Keystone endpoint with which to perform requests. In the
``[keystone]`` section, ensure that the Session- and Adapter-related options
are set.

Here is an example:

.. code-block:: ini

   [keystone]
   cafile = /path/to/ca/bundle
   valid_interfaces = internal,public
   region_name = RegionWest

See `keystoneauth documentation <https://docs.openstack.org/keystoneauth/latest>`_ for more details.

With project ID verification enabled, Designate will use the credentials
provided with the request to attempt to verify that the project ID is valid in
Keystone.

As a result of this verification, the request might return additional errors in
these cases:

- when the Keystone V3 endpoint could not be found in the service catalog
  (as specified in ``[keystone]`` section) - ``504`` error is returned
- when the authentication with incoming token was successful
  but the project id was not actually found - ``400`` is returned

For project ID validation to be successful, the user setting quotas should have
permission to list projects in Keystone. If the user does not have permission
to list projects in Keystone, the validation will be skipped.
