===
Tld
===

Tld operations.


Create Tld
==========

.. rest_method::  POST /v2/tlds

Create a tld


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
   - name: tld_name
   - description: tld_description

Request Example
---------------

.. literalinclude:: samples/tlds/create-tld-request.json
   :language: javascript



Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - name: tld_name
   - description: tld_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/tlds/tld-response.json
   :language: javascript


Show Tld
========

.. rest_method::  GET /v2/tlds/{tld_id}

Show a tld


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
   - tld_id: tld_id



Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - name: tld_name
   - description: tld_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links



Response Example
----------------

.. literalinclude:: samples/tlds/tld-response.json
   :language: javascript


List Tlds
=========

.. rest_method::  GET /v2/tlds

List the tlds associated with the Project


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
   - limit: limit
   - marker: marker
   - sort_dir: sort_dir
   - sort_key: sort_key
   - name: tld_name_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - name: tld_name
   - description: tld_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/tlds/list-tlds-response.json
   :language: javascript


Update Tld
==========

.. rest_method::  PATCH /v2/tlds/{tld_id}

Update a tld


.. rest_status_code:: success status.yaml

   - 200


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
   - tld_id: tld_id
   - name: tld_name
   - description: tld_description


Request Example
---------------

.. literalinclude:: samples/tlds/update-tld-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - name: tld_name
   - description: tld_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links



Response Example
----------------

.. literalinclude:: samples/tlds/update-tld-response.json
   :language: javascript


Delete Tld
==========

.. rest_method::  DELETE /v2/tlds/{tld_id}

Delete a tld

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
   - tld_id: tld_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
