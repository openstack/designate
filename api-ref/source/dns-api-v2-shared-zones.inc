============
Shared Zones
============

Shared zones operations.


Show a Zone Share
=================

.. rest_method::  GET /v2/zones/{zone_id}/shares/{zone_share_id}

Show a single zone share.

**New in version 2.1**

.. rest_status_code:: success status.yaml

   - 200

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
   - zone_share_id: path_zone_share_id

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - zone_id: shared_zone_id
   - project_id: project_id
   - target_project_id: target_project_id
   - created_at: created_at
   - updated_at: updated_at
   - links: links

Response Example
----------------

.. literalinclude:: samples/zones/share-zone-response.json

Get All Shared Zones
====================

.. rest_method::  GET /v2/zones/{zone_id}/shares

List all zone shares.

**New in version 2.1**

.. rest_status_code:: success status.yaml

   - 200

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
   - target_project_id: target_project_id_filter

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - zone_id: shared_zone_id
   - project_id: project_id
   - target_project_id: target_project_id
   - created_at: created_at
   - updated_at: updated_at
   - links: links

Response Example
----------------

.. literalinclude:: samples/zones/list-share-zone-response.json


Create Shared Zone
==================

.. rest_method::  POST /v2/zones/{zone_id}/shares

Share a zone with another project.

**New in version 2.1**

.. rest_status_code:: success status.yaml

   - 201

.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 409
   - 500
   - 503

Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - target_project_id: target_project_id

Request Example
---------------

.. literalinclude:: samples/zones/share-zone-request.json

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - zone_id: shared_zone_id
   - project_id: project_id
   - target_project_id: target_project_id
   - created_at: created_at
   - updated_at: updated_at
   - links: links

Response Example
----------------

.. literalinclude:: samples/zones/share-zone-response.json


Delete a Zone Share
===================

.. rest_method::  DELETE /v2/zones/{zone_id}/shares/{zone_share_id}

Delete a zone share.

**New in version 2.1**

.. rest_status_code:: success status.yaml

   - 204

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
   - zone_share_id: path_zone_share_id

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
