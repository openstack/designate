======
Quotas
======

Quota operations.


View Quotas
===========

.. rest_method::  GET /v2/quotas/{project_id}

View a projects quotas

This returns a key:value set of quotas on the system.

.. note::

   If a user is viewing another projects quotas, they will need to set
   ``x-auth-all-projects`` to ``True``


   They will need a role with the ``All-Projects`` permission to do this.


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
   - project_id: path_project_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id


Response Example
----------------

.. literalinclude:: samples/quotas/get-quotas-response.json
   :language: javascript


View Current Project's Quotas
=============================

.. rest_method::  GET /v2/quotas/

View the quotas for the current project

This returns a key:value set of quotas on the system.


.. rest_status_code:: success status.yaml

   - 200


.. rest_status_code:: error status.yaml

   - 400
   - 401
   - 403
   - 404
   - 409
   - 503


Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - project_id: path_project_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id


Response Example
----------------

.. literalinclude:: samples/quotas/get-quotas-response.json
   :language: javascript


Set Quotas
==========

.. rest_method::  PATCH /v2/quotas/{project_id}

Set a projects quotas

The request should be a key:value set of quotas to be set

This returns a key:value set of quotas on the system.

.. note::

   If a user is updating another projects quotas, they will need to set
   ``x-auth-all-projects`` to ``True``


   They will need a role with the "All-Projects" and "set-quotas"
   permission to do this.



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


Request Example
---------------

.. literalinclude:: samples/quotas/set-quotas-request.json
   :language: javascript

Request
-------

.. rest_parameters:: parameters.yaml

   - x-auth-token: x-auth-token
   - x-auth-all-projects: x-auth-all-projects
   - x-auth-sudo-project-id: x-auth-sudo-project-id
   - project_id: path_project_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id


Response Example
----------------

.. literalinclude:: samples/quotas/set-quotas-response.json
   :language: javascript





Reset Quotas
============

.. rest_method::  DELETE /v2/quotas/{project_id}

Reset all quotas for a project to default

.. note::

   If a user is resetting another projects quotas, they will need to set
   ``x-auth-all-projects`` to ``True``

   They will need a role with the ``All-Projects`` and "set-quotas"
   permission to do this.



.. rest_status_code:: success status.yaml

   - 204


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
   - project_id: path_project_id


Response Parameters
-------------------

.. rest_parameters:: parameters.yaml

   - x-openstack-request-id: x-openstack-request-id

