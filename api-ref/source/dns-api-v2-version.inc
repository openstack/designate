============
API Versions
============

Show all enabled API versions

List all API versions
=====================

.. rest_method::  GET /


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


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


