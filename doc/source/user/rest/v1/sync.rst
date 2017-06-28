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


Synchronize
===========

Overview
--------

*Note*: Synchronize is an extension and needs to be enabled before it can be
used. If Designate returns a 404 error, ensure that the following line has been
added to the designate.conf file::

    enabled_extensions_v1 = sync, ...

Trigger a synchronization of one or more resource(s) in the system.


Synchronize all domains
-----------------------

.. http:post:: /domains/sync

   Synchronize all domains

   **Example request**:

   .. sourcecode:: http

      POST /domains/sync HTTP/1.1
      Host: example.com
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

   :statuscode 200: Success
   :statuscode 401: Access Denied


Synchronize one domain
----------------------

.. http:post:: /domains/(uuid:domain_id)/sync

   Synchronize one domain

   **Example request**:

   .. sourcecode:: http

      POST /domains/1dd7851a-74e7-4ddb-b6e8-38a610956bd5/sync HTTP/1.1
      Host: example.com
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

   :statuscode 200: Success
   :statuscode 401: Access Denied


Synchronize one record
----------------------

.. http:post:: /domains/(uuid:domain_id)/records/(uuid:record_id)/sync

   Synchronize one record

   **Example request**:

   .. sourcecode:: http

      POST /domains/1dd7851a-74e7-4ddb-b6e8-38a610956bd5/records/1dd7851a-74e7-4ddb-b6e8-38a610956bd5/sync HTTP/1.1
      Host: example.com
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: application/json

   :statuscode 200: Success
   :statuscode 401: Access Denied