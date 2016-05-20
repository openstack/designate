===========
Zone Import
===========

Zone imports are an asynchronous operation, and there are different endpoints
to view the status and progress of an import


Create a Zone Import
====================

.. rest_method::  POST /v2/zones/tasks/imports

Import a zone.

.. note:: This POST should have no body, and the content-type should be text/dns

Normal response codes: 202

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_import_id
   - status: zone_import_status
   - zone_id: zone_import_zone_id
   - message: zone_import_message
   - project_id: project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version


Response Example
----------------

.. literalinclude:: samples/zones/create-zone-import-response.json
   :language: javascript


List all Zone Imports
=====================

.. rest_method::  GET /v2/zones/tasks/imports


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: zone_import_zone_id_filter
   - message: zone_import_message_filter
   - status: zone_import_status_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_import_id
   - status: zone_import_status
   - zone_id: zone_import_zone_id
   - project_id: project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version
   - links: links
   - metadata: metadata


Response Example
----------------

.. literalinclude:: samples/zones/list-zone-import-response.json
   :language: javascript

Show a Zone Import
==================

.. rest_method::  GET /v2/zones/tasks/imports/{zone_import_id}


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_import_id: path_zone_import_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_import_id
   - status: zone_import_status
   - zone_id: zone_import_zone_id
   - project_id: project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version
   - links: links


Response Example
----------------

.. literalinclude:: samples/zones/show-zone-import-response.json
   :language: javascript

Delete a Zone Import
====================

.. rest_method::  DELETE /v2/zones/tasks/imports/{zone_import_id}

This will just delete the record of the zone import, not the imported zone.

The zone will have to be deleted from the zone delete API


Normal response codes: 204

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_import_id: path_zone_import_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
