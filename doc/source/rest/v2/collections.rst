..
    Copyright 2014 Rackspace Hosting

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

..

Collections
===========

The following conventions apply to all collections, unless otherwise noted below.

Links
-----

    A links object will exist at the root of all Collection responses.
    At the minimum, it will contain a "self" link. If the collection
    resultset is not complete, a "next" link will be included for
    pagination.

    **Request:**

    .. sourcecode:: http

        GET /v2/zones?limit=2 HTTP/1.1
        Host: dns.provider.com
        Accept: application/json

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "zones": [{
            "status": "ACTIVE",
            "masters": [],
            "name": "example1.org.",
            "links": {
              "self": "http://dns.provider.com:9001/v2/zones/bd1b954e-69cd-4a91-99b4-0bcc08533123"
            },
            "transferred_at": null,
            "created_at": "2016-03-14T05:41:49.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-14T07:33:49.000000",
            "version": 10,
            "id": "bd1b954e-69cd-4a91-99b4-0bcc08533123",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1457940809,
            "project_id": "54c3cc0b8e21491f820fc701b83cb7fb",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          },
          { "status": "ACTIVE",
            "masters": [],
            "name": "example.com.",
            "links": {
              "self": "http://dns.provider.com:9001/v2/zones/45fd892d-7a67-4f65-9df0-87273f228d6c"
            },
            "transferred_at": null,
            "created_at": "2016-03-14T07:50:38.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-14T07:50:43.000000",
            "version": 2,
            "id": "45fd892d-7a67-4f65-9df0-87273f228d6c",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1457941838,
            "project_id": "54c3cc0b8e21491f820fc701b83cb7fb",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
        }],
        "links": {
          "self": "http://dns.provider.com:9001/v2/zones?limit=2",
          "next": "http://dns.provider.com:9001/v2/zones?limit=2&marker=45fd892d-7a67-4f65-9df0-87273f228d6c"
            },
        "metadata": {
           "total_count": 2
           }
        }

Pagination and Sorting
----------------------

    Pagination is available on all collections and is controlled
    using a combination of four optional query parameters:

    * `marker` - denotes the ID of the last item in the previous list.
    * `limit` - use to set the maximum number of items per page, use
                "max" to return the upper limit of results as defined
                by the operator. If not supplied, the default per page
                limit as defined by the operator will be used.
    * `sort_key` - sorts the results by the specified attribute

        * By default, elements will be sorted by their creation date.

    * `sort_dir` - determines whether sorted results are displayed in
                   ascending or descending order.

        * If explicitly used, the value of sort_dir must be either
          'asc' or 'desc'. Otherwise, the default is 'asc'.

    To navigate the collection, the parameters limit and marker can be
    set in the URI (e.g.?limit=100&marker=<UUID>). Items are sorted, as
    a default, by create time in ascending order.



    Collection responses will include a `links` object containing absolute
    URLs for the current and next page. These links may be omitted, or
    null, at the edges of a paginated collection.

    The following example takes a collection of zones and sorts it in
    descending order, using ID as the sort key rather than creation date.

    **Request:**

    .. sourcecode:: http

        GET /v2/zones?sort_key=id&sort_dir=desc HTTP/1.1
        Host: dns.provider.com
        Accept: application/json

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "zones": [{
            "status": "ACTIVE",
            "description": null,
            "updated_at": null,
            "ttl": 3600,
            "serial": 1405435156,
            "id": "c316def0-8599-4030-9dcd-2ce566348115",
            "name": "abc.example.net.",
            "created_at": "2014-07-15T14:39:16.000000",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "version": 1,
            "project_id": "noauth-project",
            "email": "hostmaster@example.net",
            "links": {
              "self": "http://dns.provider.com/v2/zones/c316def0-8599-4030-9dcd-2ce566348115"
            }
          },
          {
            "status": "ACTIVE",
            "description": null,
            "updated_at": "2014-07-08T20:28:31.000000",
            "ttl": 86400,
            "serial": 1404851315,
            "id": "a4e29ed3-d7a4-4e4d-945d-ce64678d3b94",
            "name": "example.com.",
            "created_at": "2014-07-08T20:28:19.000000",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "version": 1,
            "project_id": "noauth-project",
            "email": "hostmaster@example.com",
            "links": {
              "self": "http://dns.provider.com/v2/zones/a4e29ed3-d7a4-4e4d-945d-ce64678d3b94"
            }
          },
          {
            "status": "ACTIVE",
            "description": null,
            "updated_at": null,
            "ttl": 3600,
            "serial": 1405435142,
            "id": "38dbf635-45cb-4873-8300-6c273f0283c7",
            "name": "example.org.",
            "created_at": "2014-07-15T14:39:02.000000",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "version": 1,
            "project_id": "noauth-project",
            "email": "hostmaster@example.org",
            "links": {
              "self": "http://dns.provider.com/v2/zones/38dbf635-45cb-4873-8300-6c273f0283c7"
            }
          },
          {
            "status": "ACTIVE",
            "description": null,
            "updated_at": null,
            "ttl": 3600,
            "serial": 1405435099,
            "id": "13db810b-917d-4898-bc28-4d4ee370d20d",
            "name": "abc.example.com.",
            "created_at": "2014-07-15T14:38:19.000000",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "version": 1,
            "project_id": "noauth-project",
            "email": "hostmaster@example.com",
            "links": {
              "self": "http://dns.provider.com/v2/zones/13db810b-917d-4898-bc28-4d4ee370d20d"
            }
          }],
          "links": {
            "self": "https://dns.provider.com/v2/zones?sort_key=id&sort_dir=desc"
          }
        }


    This example takes the previously sorted list and displays only the middle two resources.

    .. sourcecode:: http

        GET /v2/zones?sort_key=id&sort_dir=desc&marker=c316def0-8599-4030-9dcd-2ce566348115&limit=2 HTTP/1.1
        Host: dns.provider.com
        Accept: application/json

    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "zones": [{
            "status": "ACTIVE",
            "description": null,
            "updated_at": "2014-07-08T20:28:31.000000",
            "ttl": 86400,
            "serial": 1404851315,
            "id": "a4e29ed3-d7a4-4e4d-945d-ce64678d3b94",
            "name": "example.com.",
            "created_at": "2014-07-08T20:28:19.000000",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "version": 1,
            "project_id": "noauth-project",
            "email": "hostmaster@example.com",
            "links": {
              "self": "http://dns.provider.com/v2/zones/a4e29ed3-d7a4-4e4d-945d-ce64678d3b94"
            }
          },
          {
            "status": "ACTIVE",
            "description": null,
            "updated_at": null,
            "ttl": 3600,
            "serial": 1405435142,
            "id": "38dbf635-45cb-4873-8300-6c273f0283c7",
            "name": "example.org.",
            "created_at": "2014-07-15T14:39:02.000000",
            "pool_id": "572ba08c-d929-4c70-8e42-03824bb24ca2",
            "version": 1,
            "project_id": "noauth-project",
            "email": "hostmaster@example.org",
            "links": {
              "self": "http://dns.provider.com/v2/zones/38dbf635-45cb-4873-8300-6c273f0283c7"
            }
          }],
          "links": {
            "self": "https://dns.provider.com/v2/zones?sort_key=id&sort_dir=desc&marker=c316def0-8599-4030-9dcd-2ce566348115&limit=2",
            "next": "https://dns.provider.com/v2/zones?sort_key=id&sort_dir=desc&limit=2&marker=38dbf635-45cb-4873-8300-6c273f0283c7"
          }
        }

Filtering
---------

    Filtering is available on all collections and is controlled using
    query parameters which match the name of the attribute being filtered.
    It is *not* required that all attributes are available as filter
    targets, but the majority will be.

    Currently, the following attributes support filtering:

    * **Blacklists**: pattern
    * **Recordsets**: name, type, ttl, data, description, status
    * **TLDs**: name
    * **Zones**: name, email, ttl, description, status

    Filters can be an exact match search or a wildcard search. Currently,
    wildcard search is supported using the '*' character.

    The following example takes a collection of zones and filters it
    by the "name" parameter.

    **Request:**

    .. sourcecode:: http

        GET /v2/zones?name=example.com. HTTP/1.1
        Host: dns.provider.com
        Accept: application/json


    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "zones": [{
            "status": "ACTIVE",
            "masters": [],
            "name": "example.com.",
            "links": {
               "self": "http://dns.provider.com:9001/v2/zones/45fd892d-7a67-4f65-9df0-87273f228d6c"
            },
            "transferred_at": null,
            "created_at": "2016-03-14T07:50:38.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-14T07:50:43.000000",
            "version": 2,
            "id": "45fd892d-7a67-4f65-9df0-87273f228d6c",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1457941838,
            "project_id": "54c3cc0b8e21491f820fc701b83cb7fb",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          }],
          "links": {
            "self": "http://dns.provider.com:9001/v2/zones?name=example.com."
            },
          "metadata": {
            "total_count": 1
            }
        }

    Wildcards can be placed anywhere within the query. The following example
    demonstrates the use of wildcards on the right side of a query:

    **Request:**

    .. sourcecode:: http

        GET /v2/zones?name=example* HTTP/1.1
        Host: dns.provider.com
        Accept: application/json


    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "zones": [{
            "status": "ACTIVE",
            "masters": [],
            "name": "example1.org.",
            "links": {
              "self": "http://dns.provider.com:9001/v2/zones/bd1b954e-69cd-4a91-99b4-0bcc08533123"
            },
            "transferred_at": null,
            "created_at": "2016-03-14T05:41:49.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-14T07:33:49.000000",
            "version": 10,
            "id": "bd1b954e-69cd-4a91-99b4-0bcc08533123",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1457940809,
            "project_id": "54c3cc0b8e21491f820fc701b83cb7fb",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          },
          {
            "status": "ACTIVE",
            "masters": [],
            "name": "example.com.",
            "links": {
             "self": "http://dns.provider.com:9001/v2/zones/45fd892d-7a67-4f65-9df0-87273f228d6c"
            },
            "transferred_at": null,
            "created_at": "2016-03-14T07:50:38.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-14T07:50:43.000000",
            "version": 2,
            "id": "45fd892d-7a67-4f65-9df0-87273f228d6c",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1457941838,
            "project_id": "54c3cc0b8e21491f820fc701b83cb7fb",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          }],
          "links": {
            "self": "http://dns.provider.com:9001/v2/zones?name=example%2A"
            },
          "metadata": {
            "total_count": 2
            }
        }

    This example demonstrates the use of multiple wildcards:

    **Request:**

    .. sourcecode:: http

        GET /v2/zones?name=*example* HTTP/1.1
        Host: dns.provider.com
        Accept: application/json


    **Response:**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "zones": [{
            "status": "ACTIVE",
            "masters": [],
            "name": "example.org.",
            "links": {
              "self": "http://dns.provider.com:9001/v2/zones/c991f02b-ae05-4570-bf75-73def68fe700"
            },
            "transferred_at": null,
            "created_at": "2016-03-15T05:41:45.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-15T05:41:50.000000",
            "version": 2,
            "id": "c991f02b-ae05-4570-bf75-73def68fe700",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1458020505,
            "project_id": "6b89012cdb2640c3a80b8d777d9bac16",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          },
          {
            "status": "ACTIVE",
            "masters": [],
            "name": "example1.org.",
            "links": {
              "self": "http://dns.provider.com:9001/v2/zones/0d35ce4e-f3b4-4ba7-9b94-4f9eba49018a"
            },
            "transferred_at": null,
            "created_at": "2016-03-15T05:54:24.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-15T05:54:44.000000",
            "version": 2,
            "id": "0d35ce4e-f3b4-4ba7-9b94-4f9eba49018a",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1458021264,
            "project_id": "6b89012cdb2640c3a80b8d777d9bac16",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          },
          {
            "status": "ACTIVE",
            "masters": [],
            "name": "example.com.",
            "links": {
              "self": "http://dns.provider.com:9001/v2/zones/a18eed67-806f-418c-883c-b7a8001a9fb6"
            },
            "transferred_at": null,
            "created_at": "2016-03-15T06:51:47.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-15T06:51:52.000000",
            "version": 2,
            "id": "a18eed67-806f-418c-883c-b7a8001a9fb6",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1458024707,
            "project_id": "6b89012cdb2640c3a80b8d777d9bac16",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          },
          {
            "status": "ACTIVE",
            "masters": [],
            "name": "abc.example.org.",
            "links": {
              "self": "http://dns.provider.com:9001/v2/zones/c3cf2487-6c3e-44cd-a305-d52ccb7aaebd"
            },
            "transferred_at": null,
            "created_at": "2016-03-15T06:53:13.000000",
            "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842",
            "updated_at": "2016-03-15T06:53:18.000000",
            "version": 2,
            "id": "c3cf2487-6c3e-44cd-a305-d52ccb7aaebd",
            "ttl": 3600,
            "action": "NONE",
            "attributes": {},
            "serial": 1458024793,
            "project_id": "6b89012cdb2640c3a80b8d777d9bac16",
            "type": "PRIMARY",
            "email": "hostmaster@example.com",
            "description": null
          }],
          "links": {
            "self": "http://dns.provider.com:9001/v2/zones?name=%2Aexample%2A"
            },
          "metadata": {
            "total_count": 4
            }
        }

Nested Collections
------------------

    A nested collection is a collection without a URI of it's own.
    The only current example we have of this is the "records" array
    under the RecordSet resource.

    By default, Nested Collections shall not be included in the
    listing of it's parent resource. For example, List RecordSets
    shall not include the "records" collection for each of the
    RecordSets returned.