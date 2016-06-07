==========
Blacklists
==========

The blacklist entries are used to manage blacklisted zones. If a zone
is blacklisted, then it cannot be used tocreate a zone. By default,
only an admin can manage these entries. Blacklisted zones are stored
as a regular expression (regex) pattern in the Database/Storage in
the blacklists table.


Create Blacklist
================

.. rest_method::  POST /v2/blacklists

Create a Blacklist

Normal response codes: 201

Error response codes: 409, 405,404,403,401,400,503


Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - pattern: blacklist_pattern
   - description: blacklist_description


Request Example
---------------

.. literalinclude:: samples/blacklists/create-blacklist-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - pattern: blacklist_pattern
   - description: blacklist_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/blacklists/blacklist-response.json
   :language: javascript



List Blacklists
---------------

.. rest_method::  GET /v2/blacklists

List all blacklists


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - pattern: blacklist_pattern_filter


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - pattern: blacklist_pattern
   - description: blacklist_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/blacklists/list-blacklists-response.json
   :language: javascript



Show Blacklist
==============

.. rest_method::  GET /v2/blacklists/{blacklist_id}

Show a blacklist


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - blacklist_id: blacklist_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - pattern: blacklist_pattern
   - description: blacklist_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/blacklists/blacklist-response.json
   :language: javascript



Update Blacklist
================

.. rest_method::  PATCH /v2/blacklists/{blacklist_id}

Update a Blacklist


Normal response codes: 200

Error response codes: 405,404,403,401,400,503


Request Parameters
------------------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - pattern: blacklist_pattern
   - description: blacklist_description


Request Example
---------------

.. literalinclude:: samples/blacklists/update-blacklist-request.json
   :language: javascript


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
   - id: id
   - pattern: blacklist_pattern
   - description: blacklist_description
   - created_at: created_at
   - updated_at: updated_at
   - links: links


Response Example
----------------

.. literalinclude:: samples/blacklists/update-blacklist-response.json
   :language: javascript



Delete a Blacklist
==================

.. rest_method::  DELETE /v2/blacklists/{blacklist_id}

Delete a blacklist


Normal response codes: 204

Error response codes: 405,404,403,401,400,503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - blacklist_id: blacklist_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id
