======
Limits
======

Show the limits for the current project


Get Project Limits
==================

.. rest_method::  GET /v2/limits

List project limits


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
   - max_page_limit: max_page_limit
   - max_recordset_name_length: max_recordset_name_length
   - max_recordset_records: max_recordset_records
   - max_zone_name_length: max_zone_name_length
   - max_zone_records: max_zone_records
   - max_zone_recordsets: max_zone_recordsets
   - max_zones: max_zones
   - min_ttl: min_ttl



Response Example
----------------

.. literalinclude:: samples/limits/get-limits-response.json
   :language: javascript


