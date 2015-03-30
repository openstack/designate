..
    Copyright (c) 2014 Rackspace Hosting
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

Tlds
=======

Overview
-----------------------
Tld (Top level domain) entries are used to manage the Tlds that Designate recognizes.
By default, only an admin can manage these entries.  The Tlds are stored in the :ref:`database`
in the table *tlds* and are not propagated to the :ref:`dns-backend`.  By default when
Designate starts up there are no Tlds in the database.

Tld Checks
-----------------------
When there are no Tld entries in the database, Tld checks are not enforced and
any domain/zone name can be created, as long as it adheres to the domain name schema.
When there are Tlds present in the database, then when a domain/zone is created
the name has to pass the following checks.

#. The last label in the domain/zone name must be present as a Tld entry in the database.
   e.g. If a domain/zone with the name *example.com.* is being created then the entry *com* must be present in the database.

#. The domain/zone name must not be present as a Tld entry in the database.
   e.g. If there is a Tld entry *co.uk* in the database, then a domain/zone with the name *co.uk.* cannot be created.

Create Tld
-------------

.. http:post:: /tlds

   Create a tld.  *name* is the only entry that is required.  The *name* should
   not end in a period (.).

   **Example request**:

   .. sourcecode:: http

      POST /tlds HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
          "name" : "com",
          "description" : "Tld source http://data.iana.org/TLD/tlds-alpha-by-domain.txt"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Content-Type: application/json; charset=UTF-8
      Location: http://127.0.0.1:9001/v2/tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9

      {
          "description":"Tld source http://data.iana.org/TLD/tlds-alpha-by-domain.txt",
          "links":{
            "self":"http://127.0.0.1:9001/v2/tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9"
          },
          "created_at":"2014-01-23T18:39:26.710827",
          "updated_at":null,
          "id":"5abe514c-9fb5-41e8-ab73-5ed25f8a73e9",
          "name":"com"
      }


   :form created_at: timestamp
   :form updated_at: timestamp
   :form name: tld name
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :statuscode 201: Created
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 409: Duplicate Tld

Get a Tld
-------------

.. http:get:: /tlds/(uuid:id)

   Lists a particular Tld

   **Example request**:

   .. sourcecode:: http

      GET /tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9 HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "description":"Tld source http://data.iana.org/TLD/tlds-alpha-by-domain.txt",
          "links":{
            "self":"http://127.0.0.1:9001/v2/tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9"
          },
          "created_at":"2014-01-23T18:39:26.710827",
          "updated_at":null,
          "id":"5abe514c-9fb5-41e8-ab73-5ed25f8a73e9",
          "name":"com"
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form name: tld name
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :statuscode 200: OK
   :statuscode 401: Access Denied
   :statuscode 404: Tld not found

List Tlds
------------

.. http:get:: /tlds

   Lists all tlds

   **Example request**:

   .. sourcecode:: http

      GET /tlds HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
        "tlds":[
          {
            "description":"Tld source http://data.iana.org/TLD/tlds-alpha-by-domain.txt",
            "links":{
              "self":"http://127.0.0.1:9001/v2/tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9"
            },
            "created_at":"2014-01-23T18:39:26.710827",
            "updated_at":null,
            "id":"5abe514c-9fb5-41e8-ab73-5ed25f8a73e9",
            "name":"com"
          },
          {
            "description":"Tld source http://data.iana.org/TLD/tlds-alpha-by-domain.txt",
            "links":{
              "self":"http://127.0.0.1:9001/v2/tlds/46e50ebc-1b51-41ee-bc1f-8e75a470c5be"
            },
            "created_at":"2014-01-23T19:59:53.985455",
            "updated_at":null,
            "id":"46e50ebc-1b51-41ee-bc1f-8e75a470c5be",
            "name":"net"
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

Update a Tld
---------------

.. http:patch:: /tlds/(uuid:id)

   updates a tld

   **Example request**:

   .. sourcecode:: http

      PATCH /tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9 HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
          "name" : "org",
          "description" : "Updated the name from com to org"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
          "description":"Updated the name from com to org",
          "links":{
            "self":"http://127.0.0.1:9001/v2/tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9"
          },
          "created_at":"2014-01-23T18:39:26.710827",
          "updated_at":"2014-01-23T20:35:12.449599",
          "id":"5abe514c-9fb5-41e8-ab73-5ed25f8a73e9",
          "name":"org"
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form name: tld name
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :statuscode 200: OK
   :statuscode 401: Access Denied
   :statuscode 404: Tld not found
   :statuscode 409: Duplicate Tld

Delete a Tld
---------------

.. http:delete:: /tlds/(uuid:id)

   delete a tld

   **Example request**:

   .. sourcecode:: http

      DELETE /tlds/5abe514c-9fb5-41e8-ab73-5ed25f8a73e9 HTTP/1.1
      Host: example.com

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Content
      Content-Type: application/json; charset=UTF-8
      Content-Length: 0

   :statuscode 204: No Content
   :statuscode 401: Access Denied
   :statuscode 404: Tld not found
