===================================
Zone Ownership Transfers - Requests
===================================

Designate allows users to transer ownership of a zone between projects.

The traditional route is to create a ``zone_transfer_request``, communicate
the key and ID out of band to the intended owner, and they create a
``zone_transfer_accept`` using this information, which will move the
ownership of the zone that project.


Create Zone Transfer Request
============================

.. rest_method::  POST /v2/zones/{zone_id}/tasks/transfer_requests

This creates an offer to transfer the zone to a different project.
The request can be scoped to single project if the ``project_id`` parameter is
supplied.

.. note:: This POST can have no body.


.. rest_status_code:: success status.yaml

   - 201


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
   - target_project_id: zone_transfer_request_target_project_id
   - description: description

Request Example
----------------

.. literalinclude:: samples/zones/create-zone-transfer-request-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_transfer_request_id
   - project_id: project_id
   - description: description
   - status: zone_transfer_request_status
   - zone_id: zone_transfer_request_zone_id
   - zone_name: zone_transfer_request_zone_name
   - key: zone_transfer_request_key
   - target_project_id: zone_transfer_request_target_project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version

Response Example
----------------

.. literalinclude:: samples/zones/create-zone-transfer-request-response.json
   :language: javascript


List Zone Transfer Requests
===========================

.. rest_method::  GET /v2/zones/tasks/transfer_requests

This will list all your outgoing requests, and any incoming requests that
have been scoped to your project.

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
   - status: zone_transfer_request_status_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_transfer_request_id
   - project_id: project_id
   - description: description
   - status: zone_transfer_request_status
   - zone_id: zone_transfer_request_zone_id
   - zone_name: zone_transfer_request_zone_name
   - key: zone_transfer_request_key
   - target_project_id: zone_transfer_request_target_project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version

Response Example
----------------

.. literalinclude:: samples/zones/list-zone-transfer-request-response.json
   :language: javascript



Show a Zone Transfer Request
============================

.. rest_method::  GET /v2/zones/tasks/transfer_requests/{zone_transfer_request_id}


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
   - zone_transfer_request_id: path_zone_transfer_request_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_transfer_request_id
   - project_id: project_id
   - description: description
   - status: zone_transfer_request_status
   - zone_id: zone_transfer_request_zone_id
   - zone_name: zone_transfer_request_zone_name
   - key: zone_transfer_request_key
   - target_project_id: zone_transfer_request_target_project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version

Response Example
----------------

.. literalinclude:: samples/zones/show-zone-transfer-request-response.json
   :language: javascript


Update a Zone Transfer Request
==============================

.. rest_method::  PATCH /v2/zones/tasks/transfer_requests/{zone_transfer_request_id}


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
   - zone_transfer_request_id: path_zone_transfer_request_id
   - target_project_id: zone_transfer_request_target_project_id
   - description: description

Request Example
----------------

.. literalinclude:: samples/zones/update-zone-transfer-request-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_transfer_request_id
   - project_id: project_id
   - description: description
   - status: zone_transfer_request_status
   - zone_id: zone_transfer_request_zone_id
   - zone_name: zone_transfer_request_zone_name
   - key: zone_transfer_request_key
   - target_project_id: zone_transfer_request_target_project_id
   - created_at: created_at
   - updated_at: updated_at
   - version: version

Response Example
----------------

.. literalinclude:: samples/zones/update-zone-transfer-request-response.json
   :language: javascript


Delete a Zone Transfer Request
==============================

.. rest_method::  DELETE /v2/zones/tasks/transfer_requests/{zone_transfer_request_id}


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
   - zone_transfer_request_id: path_zone_transfer_request_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id

