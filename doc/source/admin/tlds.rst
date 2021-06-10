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

Managing Top Level Domain Names
===============================

`System Administrators`_ can use top level domains (TLDs) to restrict the
domains under which users can create zones. While in the Domain Name System
the term "TLD" refers specifically to the set of domains that lie directly
below the root, such as ``.org``, in Designate a TLD can be any domain.

For example, if you want to require that users create zones ending in
``.org.``, this can be achieved by creating a single ``.org`` TLD:

.. code-block:: console

    $ openstack tld create --name org
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | created_at  | 2021-06-10T05:20:16.000000           |
    | description | None                                 |
    | id          | 9fd0a12d-511e-4024-bf76-6ec2e3e71edd |
    | name        | org                                  |
    | updated_at  | None                                 |
    +-------------+--------------------------------------+

.. note:: When using the `openstack tld` command, ensure that the FQDN that
   you enter has no trailing dot (`example.net.`).

If you now attempt to create a zone that does not lie within the ``.org`` TLD,
it will fail:

.. code-block:: console

    $ openstack zone create --email admin@test.net test.net.
    Invalid TLD

TLDs are much like an allowlist: if there are many TLDs then the
zone must exist within one of the TLDs. If no TLDs have been created in
Designate, then users can create any zone. Unlike the blacklists feature, TLDs
do not have a policy that allows priviliged users to create zones outside the
allowed TLDs.

You can modify the values for a TLD using the `set` command. You can use either
the name or the ID to specify which TLD to set:

.. code-block:: console

    $ openstack tld set org --name example.net
    +-------------+--------------------------------------+
    | Field       | Value                                |
    +-------------+--------------------------------------+
    | created_at  | 2021-06-10T05:20:16.000000           |
    | description |                                      |
    | id          | 9fd0a12d-511e-4024-bf76-6ec2e3e71edd |
    | name        | example.net                          |
    | updated_at  | 2021-06-10T07:09:45.000000           |
    +-------------+--------------------------------------+

You can delete a TLD by providing either the ID or the current name:

.. code-block:: console

    $ openstack tld delete org

This command has no output when completed successfully.

.. _System Administrators: https://docs.openstack.org/keystone/latest/admin/service-api-protection.html#system-personas
