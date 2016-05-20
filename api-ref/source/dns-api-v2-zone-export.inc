============
Zone Exports
============

Zone imports can be an asynchronous operation,
and there are different endpoints to view the status and progress of an export


Create a Zone Export
====================

.. rest_method::  POST /v2/zones/{zone_id}/tasks/exports

Export a zone.

.. note:: This POST should have no body

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
   - id: zone_export_id
   - location: zone_export_location
   - status: zone_export_status
   - zone_id: zone_export_zone_id
   - message: zone_export_message
   - project_id: project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version


Response Example
----------------

.. literalinclude:: samples/zones/create-zone-export-response.json
   :language: javascript


List all Zone Exports
=====================

.. rest_method::  GET /v2/zones/tasks/exports


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: zone_export_zone_id_filter
   - message: zone_export_message_filter
   - status: zone_export_status_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_export_id
   - location: zone_export_location
   - status: zone_export_status
   - zone_id: zone_export_zone_id
   - project_id: project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version
   - links: links
   - metadata: metadata


Response Example
----------------

.. literalinclude:: samples/zones/list-zone-export-response.json
   :language: javascript


Show a Zone Export Information
==============================

.. rest_method::  GET /v2/zones/tasks/exports/{zone_export_id}


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_export_id: path_zone_export_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_export_id
   - location: zone_export_location
   - status: zone_export_status
   - zone_id: zone_export_zone_id
   - project_id: project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version
   - links: links


Response Example
----------------

.. literalinclude:: samples/zones/show-zone-export-response.json
   :language: javascript


Retrive a Zone Export from the Designate Datastore
==================================================

.. rest_method::  GET /v2/zones/tasks/exports/{zone_export_id}/export


Normal response codes: 200

Error response codes: 405,404,403,401,400,503

.. note::
    This endpoint will send a response with a ``text/dns`` content-type.
    If the client does not include a ``Accepts: text/dns`` header the request
    will be rejected.


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_export_id: path_zone_export_id
   - accepts: zone_export_accepts


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id


Response Example
----------------

.. literalinclude:: samples/zones/show-zone-export-content.txt
   :language: text

