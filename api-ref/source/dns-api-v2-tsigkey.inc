=======
Tsigkey
=======

Transaction signatures (TSIG) is a mechanism used to secure DNS messages and
to provide secure server-to-server communication (usually between master and
slave server, but can be extended for dynamic updates as well).

Create Tsigkeys
===============

.. rest_method::  POST /v2/tsigkeys

Create a new Tsigkey

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
   - name: tsigkey_name
   - algorithm: tsigkey_algorithm
   - secret: tsigkey_secret
   - scope: tsigkey_scope
   - resource_id: resource_id


Request Example
---------------

.. literalinclude:: samples/tsigkeys/create-tsigkey-request.json
   :language: javascript

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - resource_id: resource_id
   - name: tsigkey_name
   - scope: tsigkey_scope
   - secret: tsigkey_secret
   - algorithm: tsigkey_algorithm
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/tsigkeys/tsigkey-response.json
   :language: javascript



List Tsigkeys
=============

.. rest_method::  GET /v2/tsigkeys

List all tsigkeys


.. rest_status_code:: success status.yaml

   - 200


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 503


Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - limit: limit
   - marker: marker
   - sort_dir: sort_dir
   - sort_key: sort_key
   - name: tsigkey_name_filter
   - algorithm: tsigkey_algorithm_filter
   - scope: tsigkey_scope_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - resource_id: resource_id
   - name: tsigkey_name
   - scope: tsigkey_scope
   - secret: tsigkey_secret
   - algorithm: tsigkey_algorithm
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/tsigkeys/list-tsigkeys-response.json
   :language: javascript



Show a Tsigkey
==============

.. rest_method::  GET /v2/tsigkeys/{tsigkey_id}

Show a tsigkey


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
   - tsigkey_id: tsigkey_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - resource_id: resource_id
   - name: tsigkey_name
   - scope: tsigkey_scope
   - secret: tsigkey_secret
   - algorithm: tsigkey_algorithm
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/tsigkeys/tsigkey-response.json
   :language: javascript



Update Tsigkey
================

.. rest_method::  PATCH /v2/tsigkeys/{tsigkey_id}

Update the attribute(s) of an existing tsigkey


.. rest_status_code:: success status.yaml

   - 200


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 405
   - 503


Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - name: tsigkey_name
   - algorithm: tsigkey_algorithm
   - secret: tsigkey_secret
   - scope: tsigkey_scope
   - resource_id: resource_id
   - tsigkey_id: tsigkey_id


Request Example
---------------

.. literalinclude:: samples/tsigkeys/update-tsigkey-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - resource_id: resource_id
   - name: tsigkey_name
   - scope: tsigkey_scope
   - secret: tsigkey_secret
   - algorithm: tsigkey_algorithm
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/tsigkeys/update-tsigkey-response.json
   :language: javascript



Delete a Tsigkey
================

.. rest_method::  DELETE /v2/tsigkeys/{tsigkey_id}

Delete a tsigkey


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
   - tsigkey_id: tsigkey_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
