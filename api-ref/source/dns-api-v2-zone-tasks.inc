==========
Zone Tasks
==========

Zone tasks.


Abandon Zone
============

.. rest_method::  POST /v2/zones/{zone_id}/tasks/abandon

Abandon a zone.

This removes a zone from the designate database without removing it
from the backends.

.. note:: This POST should have no body.

.. warning::
  This is a protentially dangerous operation, and should only be used if required

Normal response codes: 204

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id



Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id


Manually Trigger an Update of a Secondary Zone
==============================================

.. rest_method::  POST /v2/zones/{zone_id}/tasks/xfr

Trigger a new XFR from the upstream DNS servers

This will cause designate to query the name servers and if the version in
Designate is out of date, import the new version.

This is useful if an upstream server failed to send a notify to Designate

.. note:: This POST should have no body.

.. important:: This is only useful on SECONDARY zones.

Normal response codes: 202

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
