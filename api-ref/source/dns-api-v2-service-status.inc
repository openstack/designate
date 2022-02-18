================
Service Statuses
================

The Service Status entries are used to track the health state of the services
in the Designate system. Each service will report in it's health via RPC or
using HTTP.


List Statuses
=============

.. rest_method::  GET /v2/service_statuses

List all Services and statuses.


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


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - capabilities: capabilities
   - created_at: created_at
   - heartbeated_at: heartbeated_at
   - hostname: hostname
   - id: id
   - links: links
   - service_name: service_name
   - service_statuses: service_statuses
   - stats: stats
   - status: status
   - updated_at: updated_at


Response Example
----------------

.. literalinclude:: samples/service_status/service_status_list.json
   :language: javascript

Show a Service Status
=====================

.. rest_method::  GET /v2/service_statuses/{service_id}

Show the status of a service.


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

   - service_id: path_service_id
   - x-auth-token: x-auth-token


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - capabilities: capabilities
   - created_at: created_at
   - heartbeated_at: heartbeated_at
   - hostname: hostname
   - id: id
   - links: links
   - service_name: service_name
   - stats: stats
   - status: status
   - updated_at: updated_at


Response Example
----------------

.. literalinclude:: samples/service_status/service_status_show.json
   :language: javascript
