============
Zone Exports
============

Zone exports can be an asynchronous operation,
and there are different endpoints to view the status and progress of an export


Create a Zone Export
====================

.. rest_method::  POST /v2/zones/{zone_id}/tasks/export

Export a zone.

.. note:: This POST should have no body

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


.. rest_status_code:: success status.yaml

   - 200


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 503

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


Delete a Zone Export
====================

.. rest_method::  DELETE /v2/zones/tasks/exports/{zone_export_id}

This will just delete the record of the zone export, not the exported zone.

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
   - zone_export_id: path_zone_export_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
