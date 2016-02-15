..
    Copyright 2016 Hewlett Packard Enterprise Development Company LP
    All Rights Reserved.

       Licensed under the Apache License, Version 2.0 (the "License"); you may
       not use this file except in compliance with the License. You may obtain
       a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing, software
       distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
       WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
       License for the specific language governing permissions and limitations
       under the License.

Service Statuses
================

Overview
-----------------------
The Service Status entries are used to track the health state of the services
in the Designate system.


Get a Service Status
--------------------

.. http:get:: /service_statuses/(uuid:id)

   Lists a particular Service Status

   **Example request**:

   .. sourcecode:: http

      GET /service_statuses/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "capabilities": {},
          "created_at": "2016-03-08T09:20:23.000000",
          "heartbeated_at": "2016-03-08T09:26:18.000000",
          "hostname": "vagrant-ubuntu-trusty-64",
          "id": "769e8ca2-f71e-48be-8dee-631492c91e41",
          "links": {
              "self": "http://192.168.27.100:9001/v2/service_statuses/769e8ca2-f71e-48be-8dee-631492c91e41",
              "service_status": "http://192.168.27.100:9001/v2/service_statuses/769e8ca2-f71e-48be-8dee-631492c91e41"
          },
          "service_name": "pool_manager",
          "stats": {},
          "status": "UP",
          "updated_at": "2016-03-08T09:26:18.000000"
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :form service_name: Service name
   :form hostname: Service hostname
   :form capabilities: Service capabilities - dict of capabilities
   :form stats: Service stats - dict of stats
   :form status: Service status - UP, DOWN or WARNING
   :statuscode 200: OK
   :statuscode 401: Access Denied
   :statuscode 404: Service Status not found

List Service Statuses
---------------------

.. http:get:: /service_statuses

   Lists all Service Statuses

   **Example request**:

   .. sourcecode:: http

      GET /service_statuses HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
        "service_statuses":[
          {
              "capabilities": {},
              "created_at": "2016-03-08T09:20:23.000000",
              "heartbeated_at": "2016-03-08T09:26:18.000000",
              "hostname": "vagrant-ubuntu-trusty-64",
              "id": "769e8ca2-f71e-48be-8dee-631492c91e41",
              "links": {
                  "self": "http://192.168.27.100:9001/v2/service_statuses/769e8ca2-f71e-48be-8dee-631492c91e41",
                  "service_status": "http://192.168.27.100:9001/v2/service_statuses/769e8ca2-f71e-48be-8dee-631492c91e41"
              },
              "service_name": "pool_manager",
              "stats": {},
              "status": "UP",
              "updated_at": "2016-03-08T09:26:18.000000"
          },
          {
              "capabilities": {},
              "created_at": "2016-03-08T09:20:26.000000",
              "heartbeated_at": "2016-03-08T09:26:16.000000",
              "hostname": "vagrant-ubuntu-trusty-64",
              "id": "adcf580b-ea1c-4ebc-8a95-37ccdeed11ae",
              "links": {
                  "self": "http://192.168.27.100:9001/v2/service_statuses/adcf580b-ea1c-4ebc-8a95-37ccdeed11ae",
                  "service_status": "http://192.168.27.100:9001/v2/service_statuses/adcf580b-ea1c-4ebc-8a95-37ccdeed11ae"
              },
              "service_name": "zone_manager",
              "stats": {},
              "status": "UP",
              "updated_at": "2016-03-08T09:26:17.000000"
          }
        ],
        "links":{
          "self":"http://127.0.0.1:9001/v2/service_statuses"
        }
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :form service_name: Service name
   :form hostname: Service hostname
   :form capabilities: Service capabilities - dict of capabilities
   :form stats: Service stats - dict of stats
   :form status: Service status - UP, DOWN or WARNING
   :statuscode 200: OK
   :statuscode 401: Access Denied
