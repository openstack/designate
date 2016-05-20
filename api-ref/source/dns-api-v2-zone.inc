====
Zone
====

Zone operations.


Create Zone
===========

.. rest_method::  POST /v2/zones

Create a zone


Normal response codes: 202

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - name: zone_name
   - email: zone_email
   - ttl: zone_ttl
   - description: zone_description
   - type: zone_type


Request Example
---------------

.. literalinclude:: samples/zones/create-zone-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - pool_id: zone_pool_id
   - project_id: project_id
   - name: zone_name
   - email: zone_email
   - ttl: zone_ttl
   - serial: zone_serial
   - status: status
   - action: action
   - description: zone_description
   - masters: zone_masters
   - type: zone_type
   - transfered_at: zone_transfered_at
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links



Response Example
----------------

.. literalinclude:: samples/zones/zone-response.json
   :language: javascript



List Zones
==========

.. rest_method::  GET /v2/zones

List all zones


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - limit: limit
   - marker: marker
   - sort_dir: sort_dir
   - sort_key: sort_key
   - name: zone_name_filter
   - type: zone_type_filter
   - email: zone_email_filter
   - status: zone_status_filter
   - description: zone_description_filter
   - ttl: zone_ttl_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - pool_id: zone_pool_id
   - project_id: project_id
   - name: zone_name
   - email: zone_email
   - ttl: zone_ttl
   - serial: zone_serial
   - status: status
   - action: action
   - description: zone_description
   - masters: zone_masters
   - type: zone_type
   - transfered_at: zone_transfered_at
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links
   - metadata: metadata


Response Example
----------------

.. literalinclude:: samples/zones/list-zones-response.json
   :language: javascript


Show a Zone
===========

.. rest_method::  GET /v2/zones/{zone_id}

Show a zone


Normal response codes: 200

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
   - id: id
   - pool_id: zone_pool_id
   - project_id: project_id
   - name: zone_name
   - email: zone_email
   - ttl: zone_ttl
   - serial: zone_serial
   - status: status
   - action: action
   - description: zone_description
   - masters: zone_masters
   - type: zone_type
   - transfered_at: zone_transfered_at
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links



Response Example
----------------

.. literalinclude:: samples/zones/zone-response.json
   :language: javascript


Get the Name Servers for a Zone
===============================

.. rest_method:: GET /v2/zones/{zone_id}/nameservers

Show the nameservers for a zone

Normal response codes: 200

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
   - hostname: zone_nameserver_hostname
   - priority: zone_nameserver_priority



Response Example
----------------

.. literalinclude:: samples/zones/show-zone-nameservers-response.json
   :language: javascript




Update a Zone
=============

.. rest_method::  PATCH /v2/zones/{zone_id}

Update the attribute(s) for an existing zone.


Normal response codes: 202

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - email: zone_email_update
   - ttl: zone_ttl
   - description: zone_description


Request Example
---------------

.. literalinclude:: samples/zones/update-zone-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - pool_id: zone_pool_id
   - project_id: project_id
   - name: zone_name
   - email: zone_email
   - ttl: zone_ttl
   - serial: zone_serial
   - status: status
   - action: action
   - description: zone_description
   - masters: zone_masters
   - type: zone_type
   - transfered_at: zone_transfered_at
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links



Response Example
----------------

.. literalinclude:: samples/zones/update-zone-response.json
   :language: javascript


Delete a Zone
=============

.. rest_method::  DELETE /v2/zones/{zone_id}

Delete a zone


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
   - id: id
   - pool_id: zone_pool_id
   - project_id: project_id
   - name: zone_name
   - email: zone_email
   - ttl: zone_ttl
   - serial: zone_serial
   - status: status
   - action: action
   - description: zone_description
   - masters: zone_masters
   - type: zone_type
   - transfered_at: zone_transfered_at
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/zones/delete-zone-response.json
   :language: javascript
