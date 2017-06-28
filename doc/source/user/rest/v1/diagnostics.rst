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


Diagnostics
===========

Overview
--------

*Note*: Diagnostics is an extension and needs to be enabled before it can be
used. If Designate returns a 404 error, ensure that the following line has been
added to the designate.conf file::

    enabled_extensions_v1 = diagnostic, ...

Diagnose parts of the system.


Ping a host on a RPC topic
--------------------------

.. http:get:: /diagnostics/ping/(topic)/(host)

   Ping a host on a RPC topic

   **Example request**:

   .. sourcecode:: http

      GET /diagnostics/ping/agents/msdns-1 HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Vary: Accept
        Content-Type: application/json

        {
          "host": "rpc-hostname",
          "status": true,
          "backend": "msdns",
          "storage": {"status": true, "message": "..."}
        }

   :statuscode 200: Success
   :statuscode 401: Access Denied