=====
Pools
=====

Get information about the pools in a designate install


List all Pools
==============

.. rest_method::  GET /v2/pools

Get the list of Pools.


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


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - description: description
   - id: pool_id
   - attributes: pool_attributes
   - project_id: project_id
   - ns_records: pool_ns_records
   - name: pool_name
   - created_at: created_at
   - updated_at: updated_at
   - links: links
   - metadata: metadata



Response Example
----------------

.. literalinclude:: samples/pools/list-pools-response.json
   :language: javascript


Show a Pool
===========

.. rest_method::  GET /v2/pools/{pool_id}

Get a specific Pool


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


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
   - pool_id: path_pool_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - description: description
   - id: pool_id
   - attributes: pool_attributes
   - project_id: project_id
   - ns_records: pool_ns_records
   - name: pool_name
   - created_at: created_at
   - updated_at: updated_at
   - links: links
   - metadata: metadata



Response Example
----------------

.. literalinclude:: samples/pools/show-pool-response.json
   :language: javascript
