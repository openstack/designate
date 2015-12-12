..
    Copyright 2015 Hewlett-Packard Development Company, L.P.
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

Limits
======

Overview
-------------------
This endpoint is used to retrieve current limits.


Get Limits
----------

.. http:get:: /limits

   Lists current limits

   **Example request**:

   .. sourcecode:: http

      GET /limits HTTP/1.1
      Host: example.com
      Accept: application/json

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=UTF-8

      {
        "max_page_limit": 1000,
        "max_recordset_name_length": 255,
        "max_recordset_records": 20,
        "max_zone_name_length": 255,
        "max_zone_records": 500,
        "max_zone_recordsets": 500,
        "max_zones": 10,
        "min_ttl": null
      }


   :form max_page_limit: Max limit for paging
   :form max_recordset_name_length: Max length for a RecordSet name
   :form max_recordset_records: Max number RecordSet of Records
   :form max_zone_name_length: Max length for a Zone name
   :form max_zone_records: Max number of Records in a Zone
   :form max_zone_recordsets: Max number of RecordSets in a Zone
   :form max_zones: Max number of Zones
   :form max_ttl: Max TTL
   :statuscode 200: OK
