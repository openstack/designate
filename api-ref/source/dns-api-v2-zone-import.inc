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

.. rest_status_code:: success status.yaml

   - 202


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 409
   - 503


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


.. rest_status_code:: success status.yaml

   - 200


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

.. rest_status_code:: success status.yaml

   - 200


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
   - zone_import_id: path_zone_import_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
