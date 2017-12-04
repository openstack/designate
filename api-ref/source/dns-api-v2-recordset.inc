==========
Recordsets
==========

Recordsets operations.


Create Recordset
================

.. rest_method::  POST /v2/zones/{zone_id}/recordsets

Create a recordset in a zone


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
   - name: recordset_name
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

.. rest_method::  GET /v2/zones/{zone_id}/recordsets/{recordset_id}

Show an single recordset


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

.. rest_method::  PUT /v2/zones/{zone_id}/recordsets/{recordset_id}

Update a recordset


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
   - x-designate-edit-managed-records: x-designate-edit-managed-records
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

.. rest_method::  DELETE /v2/zones/{zone_id}/recordsets/{recordset_id}

Delete a recordset


.. rest_status_code:: success status.yaml

   - 202


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
   - x-designate-edit-managed-records: x-designate-edit-managed-records
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


Create a MX Recordset
=====================

.. rest_method::  POST /v2/zones/{zone_id}/recordsets

Create a MX recordset in a zone

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
   - x-designate-edit-managed-records: x-designate-edit-managed-records
   - zone_id: path_zone_id
   - name: recordset_name
   - ttl: recordset_ttl
   - description: recordset_description
   - type: recordset_type
   - records: recordset_records


Request Example
---------------

.. literalinclude:: samples/recordsets/create-mx-recordset-request.json
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

.. literalinclude:: samples/recordsets/create-mx-recordset-response.json
   :language: javascript


Create a SSHFP Recordset
========================

.. rest_method::  POST /v2/zones/{zone_id}/recordsets

Create a SSHFP recordset in a zone


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
   - name: recordset_name
   - ttl: recordset_ttl
   - description: recordset_description
   - type: recordset_type
   - records: recordset_records


Request Example
---------------

.. literalinclude:: samples/recordsets/create-sshfp-recordset-request.json
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

.. literalinclude:: samples/recordsets/create-sshfp-recordset-response.json
   :language: javascript


Create a SPF Recordset
======================

.. rest_method::  POST /v2/zones/{zone_id}/recordsets

Create a SPF recordset in a zone

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
   - name: recordset_name
   - ttl: recordset_ttl
   - description: recordset_description
   - type: recordset_type
   - records: recordset_records


Request Example
---------------

.. literalinclude:: samples/recordsets/create-spf-recordset-request.json
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

.. literalinclude:: samples/recordsets/create-spf-recordset-response.json
   :language: javascript


Create a SRV Recordset
======================

.. rest_method::  POST /v2/zones/{zone_id}/recordsets

Create a SRV recordset in a zone

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
   - name: recordset_name
   - ttl: recordset_ttl
   - description: recordset_description
   - type: recordset_type
   - records: recordset_records


Request Example
---------------

.. literalinclude:: samples/recordsets/create-srv-recordset-request.json
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

.. literalinclude:: samples/recordsets/create-srv-recordset-response.json
   :language: javascript
