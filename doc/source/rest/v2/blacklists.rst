..
    Copyright (c) 2014 Rackspace Hosting
    All Rights Reserved.

    Author: Betsy Luzader <betsy.luzader@rackspace.com>

       Licensed under the Apache License, Version 2.0 (the "License"); you may
       not use this file except in compliance with the License. You may obtain
       a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing, software
       distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
       WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
       License for the specific language governing permissions and limitations
       under the License.

Blacklists
==========

Overview
-------------------
The blacklist entries are used to manage blacklisted zones. If a zone is blacklisted, then it cannot be used to
create a zone. By default, only an admin can manage these entries. Blacklisted zones are stored as a regular expression
(regex) pattern in the :ref:`database` in the *blacklists* table.

Blacklist Checks
-------------------
Every time a new zone is created, that domain name is checked against the blacklisted zones in the database.
If it matches the regex pattern, then a 400 is returned with the message "Blacklisted domain name". If there
is no match, then the zone is created. When a new blacklisted pattern is added, it will catch any matching
new zones, but it does not check for existing zones that match the blacklisted pattern.

Regular Expressions
-------------------
Any valid regular expression may be added to the blacklists table. Here are some examples:

#. ``^example\\.com\\.$``
    This will block the "example.com." domain, but will not block any sub-domains, e.g. "my.example.com." or anything
    else containing example.com, such as, "myexample.com."

#. ``^([A-Za-z0-9_\-]+\\.)*example\\.com\\.$``
    This will block "example.com." and all sub-domains, e.g. "my.example.com.", but anything else containing
    example.com, will not be blocked, such as, "myexample.com."

*NOTE:* When using regular expressions in json, the '\\' character needs to be escaped with an additional '\\', so it
needs to be written as "^example\\\\.com\\\\.$"

Create a Blacklist
------------------

.. http:post:: /blacklists

   Create a blacklist. *pattern* is the only entry that is required. The domain name part of the pattern
   should end in a period (.).'

   **Example request**:

   .. sourcecode:: http

      POST /blacklists HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "pattern" : "^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
        "description" : "This is a blacklisted domain."
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Content-Type: application/json; charset=UTF-8
      Location: 127.0.0.1:9001/v2/blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd

      {
          "description":"This is a blacklisted domain.",
          "links":{
              "self":"http://127.0.0.1:9001/v2/blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd"
          },
          "pattern":"^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
          "created_at":"2014-03-11T21:54:57.000000",
          "updated_at":null,
          "id":"c47229fb-0831-4b55-a5b5-380d361be4bd"
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form pattern: blacklist regular expression
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :statuscode 201: Created
   :statuscode 401: Access Denied
   :statuscode 400: Invalid Object
   :statuscode 409: Duplicate Blacklist

Get a Blacklist
---------------

.. http:get:: /blacklists/(uuid:id)

   Lists a particular Blacklisted domain

   **Example request**:

   .. sourcecode:: http

      GET /blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
        "description":"This is a blacklisted domain.",
        "links":{
          "self":"http://127.0.0.1:9001/v2/blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd"
        },
        "pattern":"^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
        "created_at":"2014-03-11T21:54:57.000000",
        "updated_at":null,
        "id":"c47229fb-0831-4b55-a5b5-380d361be4bd"
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form pattern: blacklist regular expression
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :statuscode 200: OK
   :statuscode 401: Access Denied
   :statuscode 404: Blacklist not found

List Blacklists
---------------

.. http:get:: /blacklists

   Lists all blacklists

   **Example request**:

   .. sourcecode:: http

      GET /blacklists HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
        "blacklists":[
          {
          "description": "This is a blacklisted domain.",
          "links":{
            "self":"http://127.0.0.1:9001/v2/blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd"
          },
          "pattern":"^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
          "created_at":"2014-03-11T21:54:57.000000",
          "updated_at":null,
          "id":"c47229fb-0831-4b55-a5b5-380d361be4bd"
          },
          {
            "description": null,
            "links":{
              "self":"http://127.0.0.1:9001/v2/blacklists/61140aff-e2c8-488b-9bf4-da710ec8732b"
            },
            "pattern" : "^examples\\.com\\.$",
            "created_at":"2014-03-07T21:05:59.000000",
            "updated_at":null,
            "id":"61140aff-e2c8-488b-9bf4-da710ec8732b"
          }
        ],
        "links":{
          "self":"http://127.0.0.1:9001/v2/blacklists"
        }
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form pattern: blacklist regular expression
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :statuscode 200: OK
   :statuscode 401: Access Denied

Update a Blacklist
------------------

.. http:patch:: /blacklists/(uuid:id)

   updates a blacklist

   **Example request**:

   .. sourcecode:: http

      PATCH blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd HTTP/1.1
      Host: example.com
      Accept: application/json
      Content-Type: application/json

      {
        "pattern" : "^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
        "description" : "Updated the description"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
        "description":"Updated the pattern to catch subdomains",
        "links":{
          "self":"http://127.0.0.1:9001/v2/blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd"
        },
        "created_at":"2014-03-11T21:54:57.000000",
        "updated_at":"2014-03-13T16:49:32.117187",
        "id":"c47229fb-0831-4b55-a5b5-380d361be4bd",
        "pattern":"^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$"
      }

   :form created_at: timestamp
   :form updated_at: timestamp
   :form pattern: blacklist regular expression pattern
   :form id: uuid
   :form description: UTF-8 text field
   :form links: links to traverse the list
   :statuscode 200: OK
   :statuscode 401: Access Denied
   :statuscode 404: Blacklist not found
   :statuscode 409: Duplicate Blacklist

Delete a Blacklist
------------------

.. http:delete:: /blacklists/(uuid:id)

   delete a blacklist

   **Example request**:

   .. sourcecode:: http

      DELETE /blacklists/c47229fb-0831-4b55-a5b5-380d361be4bd HTTP/1.1
      Host: example.com

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Content
      Content-Type: application/json; charset=UTF-8
      Content-Length: 0

   :statuscode 204: No Content
   :statuscode 401: Access Denied
   :statuscode 404: Blacklist not found






