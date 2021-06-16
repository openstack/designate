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

.. rest_status_code:: success status.yaml

   - 204


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 503


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

.. rest_status_code:: success status.yaml

   - 202


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 503


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



Pool Move Zone
==============

.. rest_method::  POST /v2/zones/{zone_id}/tasks/pool_move

Move a zone to another pool.

This moves a zone from the existing designate pool to specified target pool. If
pool is not specified by admin, designate will determine suitable pool by
itself and move zone to that pool.

.. rest_status_code:: success status.yaml

   - 202


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 500
   - 503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - pool_id: zone_pool_target_id

Request Example
---------------

.. literalinclude:: samples/zones/poolmove-zone-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
