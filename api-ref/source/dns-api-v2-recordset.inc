==========
Recordsets
==========

Recordsets operations.


Create Recordset
================

.. rest_method::  POST /v2/zones/{zone_id}/recordsets

Create a recordset in a zone


Normal response codes: 202

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - ttl: recordset_ttl
   - description: recordset_description
   - type: recordset_type
   - records: recordset_records


Request Example
---------------

.. literalinclude:: samples/recordsets/create-recordset-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - project_id: project_id
   - name: recordset_name
   - ttl: recordset_ttl
   - status: status
   - action: action
   - zone_id: recordset_zone_id
   - zone_name: recordset_zone_name
   - description: recordset_description
   - type: recordset_type
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/recordsets/create-recordset-response.json
   :language: javascript


List Recordsets in a Zone
=========================

.. rest_method::  GET /v2/zones/{zone_id}/recordsets

This lists all recordsets in a zone


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - limit: limit
   - marker: marker
   - sort_dir: sort_dir
   - sort_key: sort_key
   - name: recordset_name_filter
   - type: recordset_type_filter
   - ttl: recordset_ttl_filter
   - data: recordset_data_filter
   - status: recordset_status_filter
   - description: recordset_description_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - project_id: project_id
   - name: recordset_name
   - ttl: recordset_ttl
   - status: status
   - action: action
   - zone_id: recordset_zone_id
   - zone_name: recordset_zone_name
   - description: recordset_description
   - type: recordset_type
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links
   - metadata: metadata



Response Example
----------------

.. literalinclude:: samples/recordsets/list-recordset-in-zone-response.json
   :language: javascript


List all Recordsets owned by project
====================================

.. rest_method::  GET /v2/recordsets

This lists all recordsets owned by a project in Designate

Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - limit: limit
   - marker: marker
   - sort_dir: sort_dir
   - sort_key: sort_key
   - name: recordset_name_filter
   - type: recordset_type_filter
   - ttl: recordset_ttl_filter
   - data: recordset_data_filter
   - status: recordset_status_filter
   - description: recordset_description_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - project_id: project_id
   - name: recordset_name
   - ttl: recordset_ttl
   - status: status
   - action: action
   - zone_id: recordset_zone_id
   - zone_name: recordset_zone_name
   - description: recordset_description
   - type: recordset_type
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links
   - metadata: metadata


Response Example
----------------

.. literalinclude:: samples/recordsets/list-all-recordset-response.json
   :language: javascript


Show a Recordset
================

.. rest_method::  GET /v2/recordsets/{zone_id}/{recordset_id}

Show an single recordset

Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - recordset_id: path_recordset_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - project_id: project_id
   - name: recordset_name
   - ttl: recordset_ttl
   - status: status
   - action: action
   - zone_id: recordset_zone_id
   - zone_name: recordset_zone_name
   - description: recordset_description
   - type: recordset_type
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/recordsets/show-recordset-response.json
   :language: javascript


Update a Recordset
==================

.. rest_method::  PATCH /v2/zone/{zone_id}/recordsets/{recordset_id}

Update a recordset

Normal response codes: 202

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - recordset_id: path_recordset_id
   - ttl: recordset_ttl
   - description: recordset_description
   - records: recordset_records

Request Example
---------------

.. literalinclude:: samples/recordsets/update-recordset-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - project_id: project_id
   - name: recordset_name
   - ttl: recordset_ttl
   - status: status
   - action: action
   - zone_id: recordset_zone_id
   - zone_name: recordset_zone_name
   - description: recordset_description
   - type: recordset_type
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/recordsets/update-recordset-response.json
   :language: javascript


Delete a Recordset
==================

.. rest_method::  DELETE /v2/zone/{zone_id}/recordsets/{recordset_id}

Delete a recordset

Normal response codes: 202

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - zone_id: path_zone_id
   - recordset_id: path_recordset_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - project_id: project_id
   - name: recordset_name
   - ttl: recordset_ttl
   - status: status
   - action: action
   - zone_id: recordset_zone_id
   - zone_name: recordset_zone_name
   - description: recordset_description
   - type: recordset_type
   - version: version
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/recordsets/update-recordset-response.json
   :language: javascript

