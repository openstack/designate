..
    Copyright 2015 Hewlett-Packard Development Company, L.P.
    All Rights Reserved.

    Author: Endre Karlson <endre.karlson@hpe.com>

       Licensed under the Apache License, Version 2.0 (the "License"); you may
       not use this file except in compliance with the License. You may obtain
       a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing, software
       distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
       WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
       License for the specific language governing permissions and limitations
       under the License.

.. note:

  Currently the /reverse endpoint is used to tie reverse DNS records to IPs.

FloatingIPs
===========

In order to use the FloatingIPs functionality you will need to have a FloatingIP
associated to your project in Neutron.

Set  FloatingIP's PTR record
----------------------------

.. http:patch:: /reverse/floatingips/(string:region):(uuid:floatingip_id)

   Set a PTR record for the given FloatingIP. The domain if it does not exist
   will be provisioned automatically.

   **Example request**:

   .. sourcecode:: http

      POST /reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "ptrdname" : "smtp.example.com.",
        "description" : "This is a floating ip for 10.0.0.1",
        "ttl": 600
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 202 Created
      Content-Type: application/json; charset=UTF-8
      Location: http://example.com:9001/v2/reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd

      {
          "ptrdname": "smtp.example.com.",
          "ttl": 600,
          "description":"This is a floating ip for 172.24.4.3",
          "address": "172.24.4.3",
          "action": "CREATE",
          "status": "PENDING",
          "links":{
              "self":"http://example.com:9001/v2/reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd"
          },
          "pattern":"smtp.example.com.",
          "created_at":"2014-03-11T21:54:57.000000",
          "updated_at":null,
          "id":"RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd",
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form ptrdname: Hostname
   :form ttl: Time to live
   :form address: The FloatingIP address
   :form id: A combination of the Region and FloatingIP ID
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :form action: Provisioning Action
   :form status: Provisioning Status
   :statuscode 202: Created
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: FloatingIP / PTR Not found


Get a FloatingIP's PTR record
-----------------------------

.. http:get:: /reverse/floatingips/(string:region):(uuid:floatingip_id)

  Shows a particular FloatingIP PTR

  **Example request**:

  .. sourcecode:: http

     GET /reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd HTTP/1.1
     Host: example.com
     Accept: application/json

  **Example response**:

  .. sourcecode:: http

     HTTP/1.1 200 OK
     Content-Type: application/json; charset=UTF-8

     {
         "ptrdname": "smtp.example.com.",
         "ttl": 600,
         "description":"This is a floating ip for 172.24.4.3",
         "address": "172.24.4.3",
         "action": "NONE",
         "status": "ACTIVE",
         "links":{
             "self":"http://example.com:9001/v2/reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd"
         },
         "pattern":"smtp.example.com.",
         "created_at":"2014-03-11T21:54:57.000000",
         "updated_at":null,
         "id":"RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd",
     }

  :form created_at: timestamp
  :form updated_at: timestamp
  :form ptrdname: Hostname
  :form ttl: Time to live
  :form address: The FloatingIP address
  :form id: A combination of the Region and FloatingIP ID
  :form description: UTF-8 text field
  :form links: links to traverse the list
  :form action: Provisioning Action
  :form status: Provisioning Status
  :statuscode 200: OK
  :statuscode 404: FloatingIP or PTR not found not found

List FloatingIP PTR records
---------------------------

.. http:get:: /reverse/floatingips/

  Lists all FloatingIPs PTR records

  **Example request**:

  .. sourcecode:: http

     GET /reverse/floatingips/ HTTP/1.1
     Host: example.com
     Accept: application/json

  **Example response**:

  .. sourcecode:: http

     HTTP/1.1 200 OK
     Content-Type: application/json; charset=UTF-8

     {
       "floatingips":[
         {
             "ttl": 600,
             "ptrdname": "smtp.example.com.",
             "description":"This is a floating ip for 172.24.4.3",
             "address": "172.24.4.3",
             "action": "NONE",
             "status": "ACTIVE",
             "links":{
                 "self":"http://example.com:9001/v2/reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd"
             },
             "pattern":"smtp.example.com.",
             "created_at":"2014-03-11T21:54:57.000000",
             "updated_at":null,
             "id":"RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd",
         },
         {
             "ptrdname": "www.example.com.",
             "ttl": 600,
             "description":"This is a floating ip for 172.24.4.4",
             "address": "172.24.4.4",
             "action": "NONE",
             "status": "ACTIVE",
             "links":{
                 "self":"http://example.com:9001/v2/reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4be"
             },
             "pattern":"smtp.example.com.",
             "created_at":"2014-03-11T21:54:57.000000",
             "updated_at":null,
             "id":"RegionOne:c47229fb-0831-4b55-a5b5-380d361be4be",
         }
       ],
       "links":{
         "self":"http://127.0.0.1:9001/v2/tlds"
       }
     }

  :form created_at: timestamp
  :form updated_at: timestamp
  :form name: tld name
  :form id: uuid
  :form description: UTF-8 text field
  :form links: links to traverse the list
  :statuscode 200: OK
  :statuscode 401: Access Denied


Unset the PTR record for a FloatingIP
-------------------------------------

.. http:patch:: /reverse/floatingips/(string:region):(uuid:floatingip_id)

   Unset a PTR record for the given FloatingIP.

   **Example request**:

   .. sourcecode:: http

      PATCH /reverse/floatingips/RegionOne:c47229fb-0831-4b55-a5b5-380d361be4bd HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "ptrdname" : null,
      }

   :statuscode 202: Pending
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 404: FloatingIP / PTR Not found
