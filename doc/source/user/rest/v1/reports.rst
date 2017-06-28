..
    Copyright 2014 Hewlett-Packard Development Company, L.P.

    Author: Endre Karlson <endre.karlson@hp.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


Reports
=======

Overview
--------

*Note*: Reports is an extension and needs to be enabled before it can be
used. If Designate returns a 404 error, ensure that the following line has been
added to the designate.conf file::

    enabled_extensions_v1 = reports, ...

Reports about things in the system


Get all tenants
---------------

.. http:get:: /reports/tenants

   Fetch all tenants

   **Example request**:

   .. sourcecode:: http

      GET /reports/tenants HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
        "tenants": [{
            "domain_count": 2,
            "id": "71ee6d049a49435c8f7dd002cfe08d96"
        }]
      }

   :form tenants: List of tenants
   :statuscode 200: Success
   :statuscode 401: Access Denied

Report tenant resources
-----------------------

.. http:get:: /reports/tenants/(tenant_id)

   Report tenant resources

   **Example request**:

   .. sourcecode:: http

      GET /reports/tenants/3d8391080d4a4ec4b3eadf18e6b1539a HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
          "domain_count": 0,
          "domains": [],
          "id": "3d8391080d4a4ec4b3eadf18e6b1539a"
      }

   :param tenant_id: Tenant Id to get reports for
   :type tenant_id: string
   :form domain_count: integer
   :form domains: Server hostname
   :form id: Tenant Id
   :statuscode 200: Success
   :statuscode 401: Access Denied

Report resource counts
----------------------

.. http:get:: /reports/counts

   Report resource counts

   **Example request**:

   .. sourcecode:: http

      GET /reports/counts HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
          "domains": 0,
          "records": 0,
          "tenants": 0
      }

   :form domains: Domains count
   :form records: Records count
   :form tenants: Tenants count
   :statuscode 200: Success
   :statuscode 401: Access Denied

Report tenant counts
----------------------

.. http:get:: /reports/counts/tenants

   Report tenant counts

   **Example request**:

   .. sourcecode:: http

      GET /reports/counts/tenants HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
          "tenants": 0
      }



   :form tenants: Tenants count
   :statuscode 200: Success
   :statuscode 401: Access Denied

Report domain counts
----------------------

.. http:get:: /reports/counts/domains

   Report domain counts

   **Example request**:

   .. sourcecode:: http

      GET /reports/counts/domains HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
          "domains": 0
      }



   :form domains: Domains count
   :statuscode 200: Success
   :statuscode 401: Access Denied

Report record counts
----------------------

.. http:get:: /reports/counts/records

   Report record counts

   **Example request**:

   .. sourcecode:: http

      GET /reports/counts/records HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

      {
          "records": 0
      }



   :form records: Records count
   :statuscode 200: Success
   :statuscode 401: Access Denied