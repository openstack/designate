..
    Copyright 2016 Rackspace Inc.

    Author: Tim Simmons <tim.simmons@rackspace.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Blacklisting Domain Names
=========================

.. note::

    The blacklist feature will be renamed and moved to
    denylist in the near future.

You can prevent users from creating zones with names that match a particular
regular expression using blacklists. For example, you might use a blacklist to
prevent users from:

- creating a specific zone.
- creating zones that contain a certain string,
- creating subzones of a certain zone.

Managing Blacklists
-------------------

You can create blacklists using the ``zone blacklist create`` command with
`System Administrator`_ privileges. For example, to blacklist ``example.com.``
and all of its subdomains:

.. code-block:: console

  $ openstack zone blacklist create --pattern ".*example.com."
  +-------------+--------------------------------------+
  | Field       | Value                                |
  +-------------+--------------------------------------+
  | created_at  | 2021-05-27T04:06:42.000000           |
  | description | None                                 |
  | id          | 7622e241-8c3d-4c03-a692-8747e3cf2658 |
  | pattern     | .*example.com.                       |
  | updated_at  | None                                 |
  +-------------+--------------------------------------+

If a `Domain or Project Persona`_ attempts to create ``foo.example.com.``, or
``example.com.``, they encounter an error:

.. code-block:: console

  $ openstack zone create --email admin@example.com example.com.
  Blacklisted zone name
  $ openstack zone create --email admin@example.com foo.example.com.
  Blacklisted zone name

.. note::

   Users who satisfy the ``use_blacklisted_zone`` policy can create zones with
   names that are on a blacklist. By default, the only users who have this
   override are `System Administrators`_.

You can update a blacklist using ``zone blacklist set`` to modify its pattern
or description;

.. code-block:: console

  $ openstack zone blacklist set 81fbfe02-6bf9-4812-a40e-1522ab6862ca --pattern ".*web.example.com"
  +-------------+--------------------------------------+
  | Field       | Value                                |
  +-------------+--------------------------------------+
  | created_at  | 2021-05-27T04:14:14.000000           |
  | description | None                                 |
  | id          | 81fbfe02-6bf9-4812-a40e-1522ab6862ca |
  | pattern     | .*web.example.com                    |
  | updated_at  | 2021-05-27T04:14:48.000000           |
  +-------------+--------------------------------------+

You can delete a blacklist using `zone blacklist delete`:

.. code-block:: console

  $ openstack zone blacklist delete 7622e241-8c3d-4c03-a692-8747e3cf2658

There is no output when this command is successful.


Using the REST API
-------------------

The regular expressions used for blacklists are similar to Python regular
expressions, but you must escape certain characters when making HTTP calls.

For examples, this refex restricts using ``example.com.`` and its ASCII
subdomains:

``^([A-Za-z0-9_\\-]+\.)*example\.com\.$``

However, you must insert the escape character (backslash, \) before the
instances of dot (.) and .com:

``^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$``


Here is the API call and the regex with the HTTP characters escaped:

.. code-block:: http

  POST /v2/blacklists/ HTTP/1.1
  Accept: application/json
  Content-Type: application/json

  {
    "pattern" : "^([A-Za-z0-9_\\-]+\\.)*example\\.com\\.$",
    "description" : "This blacklists *.example.com."
  }


Regular Expressions
-------------------

Regular Expressions can be difficult to work with. The
`Python Regex Documentation`_ may serve as a useful introduction, and online
regular expression tools can assist when building and testing regexes for use
with the blacklist API.

.. _System Administrator: personas_
.. _System Administrators: personas_
.. _Domain or Project Persona: personas_
.. _Python Regex Documentation: https://docs.python.org/3/howto/regex.html#regex-howto
.. _personas: https://docs.openstack.org/keystone/latest/admin/service-api-protection.html#system-personas
