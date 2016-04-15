..
    Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _tempest:

=======
Tempest
=======

The Designate team maintains a set of tempest tests to exercise the Designate
service and APIs.

Intro and References
====================
* `Tempest Docs`_ - Tempest docs
* `Tempest HACKING`_ - General tempest style and coding guidelines
* `Tempest Plugins`_ - Tempest Test Plugin Interface guide

Quick Start
===========

To run all tests from this plugin, install the plugin into your environment
and from the tempest repo, run::

    $ tox -e all-plugin -- designate

To run a single test case, run with the test case name, for example::

    $ tox -e all-plugin -- designate_tempest_plugin.tests.api.v2.test_zones.ZonesAdminTest.test_get_other_tenant_zone

To run all tempest tests including this plugin, run::

    $ tox -e all-plugin

Writing new tests
=================

Writing new tests is easy, and we encourage contributers to write tests for
any new or changed functionality. Most of the patterns you will find in the
Designate tests will look familar if you have contributed to tempest, so rather
than re-type all their docs here, please have a read of the `Tempest Docs`_.

Test Clients
------------

In Tempest tests, it is forbidden to use a services python bindings or client,
as doing so would allow API changes to go unnoticed when the server and client
are updated. As such, each service is expected to have a minimal in-tree
client. Designate's client can be found in:

.. code-block:: bash

   $ tree -P "*_client.py" designate_tempest_plugin/services/dns/

   designate_tempest_plugin/services/dns/
   ├── json
   │   └── versions_client.py
   └── v2
       └── json
           ├── recordsets_client.py
           └── zones_client.py

An example client, in this case for a subset of /v2/zones is included below:

.. code-block:: python

   class ZonesClient(base.DnsClientV2Base):
   """API V2 Tempest REST client for Designate API"""

   @base.handle_errors
   def create_zone(self, name=None, email=None, ttl=None, description=None,
                   wait_until=False, params=None):
       """Create a zone with the specified parameters.

       :param name: The name of the zone.
           Default: Random Value
       :param email: The email for the zone.
           Default: Random Value
       :param ttl: The ttl for the zone.
           Default: Random Value
       :param description: A description of the zone.
           Default: Random Value
       :param wait_until: Block until the zone reaches the desiered status
       :param params: A Python dict that represents the query paramaters to
                      include in the request URI.
       :return: A tuple with the server response and the created zone.
       """
       zone = {
           'name': name or dns_data_utils.rand_zone_name(),
           'email': email or dns_data_utils.rand_email(),
           'ttl': ttl or dns_data_utils.rand_ttl(),
           'description': description or data_utils.rand_name('test-zone'),
       }

       resp, body = self._create_request('zones', zone, params=params)

       if wait_until:
           waiters.wait_for_zone_status(self, body['id'], wait_until)

       return resp, body

Some items to note, client methods should be wrapped in the
`base.handle_errors` decorator, which is used to allow for ignoring certain
types of errors, in certain cases. Most commonly, this will be ignoring 404's
when cleaning up resources.

Test Cases
----------

Designate's tests can be found in:

.. code-block:: bash

   $ tree -P "test_*.py" designate_tempest_plugin/tests/

   designate_tempest_plugin/tests/
   ├── api
   │   ├── test_versions.py
   │   └── v2
   │       ├── test_recordsets.py
   │       └── test_zones.py
   └── scenario
       └── v2
           ├── test_recordsets.py
           └── test_zones.py

There are two groupings of tests here "api" and "scenario". **API tests**
should be quick, and simple. Testing as small a surface area of the API as is
possible while still getting the job done. Additionally, API tests should avoid
waiting for resources to become ACTIVE etc, as this typically pushes test time
out significantly, and would only duplicate scenario tests. **Scenario tests**
should cover common real world uses cases. For example, creating a zone,
waiting for it to become ACTIVE, adding some records, waiting for ACTIVE,
querying the DNS servers themselves, and finally deleting the zone and waiting
for it to 404.

An example test, in this case for a subset of /v2/zones functionality is
included below:

.. code-block:: python

   class ZonesTest(BaseZonesTest):
       @classmethod
       def setup_clients(cls):
           super(ZonesTest, cls).setup_clients()

           cls.client = cls.os.zones_client

       @test.attr(type='smoke')
       @test.idempotent_id('fbabd6af-238a-462e-b923-de4d736b90a7')
       def test_create_zone(self):
           LOG.info('Create a zone')
           _, zone = self.client.create_zone()
           self.addCleanup(self.client.delete_zone, zone['id'])

           LOG.info('Ensure we respond with CREATE+PENDING')
           self.assertEqual('CREATE', zone['action'])
           self.assertEqual('PENDING', zone['status'])

           LOG.info('Ensure the fetched response matches the created zone')
           self._assertExpected(zone, body)


Test Cases - Alternative Credentials
------------------------------------

Some tests require more than just a "standard" cloud user, e.g. those tests
checking admin only functionality. We can ensure both user and admin
credentials are available using the class level "credentials" property like so:


.. code-block:: python

   class ZonesAdminTest(BaseZonesTest):
       credentials = ['primary', 'admin']

       @classmethod
       def setup_clients(cls):
           super(ZonesAdminTest, cls).setup_clients()

           cls.client = cls.os.zones_client
           cls.adm_client = cls.os_adm.zones_client

       @test.idempotent_id('6477f92d-70ba-46eb-bd6c-fc50c405e222')
       def test_get_other_tenant_zone(self):
           LOG.info('Create a zone as a user')
           _, zone = self.client.create_zone()
           self.addCleanup(self.client.delete_zone, zone['id'])

           LOG.info('Fetch the zone as an admin')
           _, body = self.adm_client.show_zone(
               zone['id'], params={'all_tenants': True})

           LOG.info('Ensure the fetched response matches the created zone')
           self._assertExpected(zone, body)


Test Decorators
---------------

Several different test decorators are used within the test cases, this attempts
to explain their purpose and correct usage.


@test.idempotent_id
~~~~~~~~~~~~~~~~~~~

The `idempotent_id` decorator allows for tracking of tests even after they have
been renamed. The UUID should be randomly generated as the test is first
written, e.g. with `uuidgen` on most linux hosts, and should not be changed
when the test is renamed.

Every test should have a unique idempotent_id assigned.

Example:

.. code-block:: python

   class ZonesTest(BaseZonesTest):
       @test.idempotent_id('fbabd6af-238a-462e-b923-de4d736b90a7')
       def test_create_zone(self):
           pass


@test.attr
~~~~~~~~~~

The `attr` decorator is used to set test attributes, this is most commonly used
to set the test type. Currently, we use one test type "smoke", which should be
applied to any tests which test the most basic functionaility Designate
provides, allowing for the core functionaility to be tested quickly, without
having to run the entire suite. Another type we use is "slow", which should be
applied to tests which take on average 5 seconds or more.

Example:

.. code-block:: python

   class ZonesTest(BaseZonesTest):
       @test.attr(type='smoke')
       def test_create_zone(self):
           pass

       @test.attr(type='slow')
       def test_something_else(self):
           pass

@test.services
~~~~~~~~~~~~~~

The `services` decorator is used to indicate which services are exercised by
a given test. The `services` decorator may only be used on scenario tests, and
(for now) should not include "dns" itself. For example, given a scenario test
that interactions with Designate's Reverse DNS APIs, which in turn talk to
Neutron, we would use something like the below:

Example:

.. code-block:: python

   class ReverseTest(BaseDnsTest):
       @test.services('network')
       def test_reverse_dns_for_fips(self):
           pass


.. _Tempest Docs: http://docs.openstack.org/developer/tempest/
.. _Tempest HACKING: http://docs.openstack.org/developer/tempest/HACKING.html
.. _Tempest Plugins: http://docs.openstack.org/developer/tempest/plugin.html
