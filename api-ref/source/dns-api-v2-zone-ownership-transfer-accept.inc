==================================
Zone Ownership Transfers - Accepts
==================================

Designate allows users to transer ownership of a zone between projects.

For the final step, the receiving project has to accept the new zone, using
the ``transfer_accepts`` API


Create Zone Transfer Accept
============================

.. rest_method::  POST /v2/zones/{zone_id}/tasks/transfer_accepts

This accepts an offer of a ownership transfer


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - key: zone_transfer_request_key
   - zone_id: zone_transfer_request_id


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
   - links: links

Response Example
----------------

.. literalinclude:: samples/zones/create-zone-transfer-accept-response.json
   :language: javascript


Get Zone Transfer Accept
========================

.. rest_method::  GET /v2/zones/tasks/transfer_requests/{zone_transfer_accept_id}


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


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
   - links: links

Response Example
----------------

.. literalinclude:: samples/zones/create-zone-transfer-accept-response.json
   :language: javascript
