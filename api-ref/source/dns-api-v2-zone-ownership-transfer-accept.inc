==================================
Zone Ownership Transfers - Accepts
==================================

Designate allows users to transer ownership of a zone between projects.

For the final step, the receiving project has to accept the new zone, using
the ``transfer_accepts`` API


Create Zone Transfer Accept
============================

.. rest_method::  POST /v2/zones/tasks/transfer_accepts

This accepts an offer of a ownership transfer


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
   - key: zone_transfer_request_key
   - zone_transfer_request_id: zone_transfer_request_id


Request Example
----------------

.. literalinclude:: samples/zones/create-zone-transfer-accept-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_transfer_accept_id
   - status: zone_transfer_request_status
   - project_id: project_id
   - zone_id: zone_transfer_request_id
   - key: zone_transfer_request_key
   - created_at: created_at
   - updated_at: updated_at
   - zone_transfer_request_id: zone_transfer_request_id
   - links: links

Response Example
----------------

.. literalinclude:: samples/zones/create-zone-transfer-accept-response.json
   :language: javascript


Get Zone Transfer Accept
========================

.. rest_method::  GET /v2/zones/tasks/transfer_requests/{zone_transfer_accept_id}

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
   - zone_transfer_accept_id: path_zone_transfer_accept_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_transfer_accept_id
   - status: zone_transfer_request_status
   - project_id: project_id
   - zone_id: zone_transfer_request_id
   - key: zone_transfer_request_key
   - created_at: created_at
   - updated_at: updated_at
   - zone_transfer_request_id: zone_transfer_request_id
   - links: links

Response Example
----------------

.. literalinclude:: samples/zones/create-zone-transfer-accept-response.json
   :language: javascript


List Zone Transfer Accepts
===========================

.. rest_method::  GET /v2/zones/tasks/transfer_accepts

This will list all your accepted ownership transfer.

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
   - status: zone_transfer_accept_status_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: zone_transfer_accept_id
   - project_id: project_id
   - status: zone_transfer_request_status
   - zone_id: zone_transfer_request_id
   - key: zone_transfer_request_key
   - created_at: created_at
   - updated_at: updated_at
   - zone_transfer_request_id: zone_transfer_request_id
   - links: links
   - metadata: metadata


Response Example
----------------

.. literalinclude:: samples/zones/list-zone-transfer-accept-response.json
   :language: javascript
