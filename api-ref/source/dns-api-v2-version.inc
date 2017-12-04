============
API Versions
============

Show all enabled API versions

List all API versions
=====================

.. rest_method::  GET /


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

No parameters needed

Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id


Response Example
----------------

.. literalinclude:: samples/versions/get-versions-response.json
   :language: javascript


