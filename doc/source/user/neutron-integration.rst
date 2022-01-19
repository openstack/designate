..
    Copyright 2022 Red Hat

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.


=============================
Using DNS with Neutron & Nova
=============================

Neutron can be integrated with Designate to provide automatic
:term:`recordset` creation for ports and, by proxy, Nova server instances.
This section will describe how you can use this integration to have Designate
DNS :term:`recordsets<Recordset>` created for Neutron ports and Nova instances
at creation time.

Neutron DNS Extensions
======================

DNS integration in Neutron is optional and an extension must be enabled in the
Neutron configuration file, by a cloud administrator,  for DNS names to be
assigned automatically to Neutron and Nova resources. You can check if a DNS
integration extension is enabled by querying the `Neutron extensions API`_:

.. _Neutron extensions API: https://docs.openstack.org/api-ref/network/v2/index.html#list-extensions

.. code-block:: console

   $ openstack extension list --network -f value -c Alias | grep dns-integration
   dns-integration

One of these extensions must be enabled to allow Neutron and, via Neutron, Nova
to automatically create DNS :term:`recordsets<Recordset>` in Designate:

* dns-integration
* dns-domain-ports (includes dns-integration)
* subnet-dns-publish-fixed-ip (includes dns-integration and dns-domain-ports)
* dns-integration-domain-keywords (includes all others)

dns-integration
---------------

When the `dns-integration` extension is enabled the following DNS attributes
will be available via Neutron:

.. list-table::
   :header-rows: 1
   :widths: 30 30 30

   * - Resource
     - dns_name
     - dns_domain
   * - Ports
     - Yes
     - No
   * - Networks
     - No
     - Yes
   * - Floating IPs
     - Yes
     - Yes

dns-domain-ports
----------------

In addition, if the `dns-domain-ports` extension is enabled in Neutron, ports
can be created with a dns_domain specified. This dns_domain will take
precedence over the dns_domain setting for the network. You can check if the
`dns-domain-ports` extension is enabled by querying the
`Neutron extensions API`_:

.. code-block:: console

   $ openstack extension list --network -f value -c Alias | grep dns-domain-ports
   dns-domain-ports

With the `dns-domain-ports` extension is enabled the following DNS settings
will be available via Neutron:

.. list-table::
   :header-rows: 1
   :widths: 30 30 30

   * - Resource
     - dns_name
     - dns_domain
   * - Ports
     - Yes
     - Yes
   * - Networks
     - No
     - Yes
   * - Floating IPs
     - Yes
     - Yes

Both of these extensions impose a set of criteria for when DNS
:term:`recordsets<Recordset>` will be created in Designate.

* A `dns_domain` must be specified either on the network, port, or floating IP.
  If both the network and the port or floating IP specify a `dns_domain`, the
  `dns_domain` specified on the port or floating IP will take precedent over
  the `dns_domain` provided on the network.
* The network must not have the `router:external` field set to True.
* The network type must be one of: FLAT, VLAN, GRE, VXLAN, or GENEVE.
* For VLAN, GRE, VXLAN, or GENEVE networks, the segmentation ID must be outside
  the ranges configured in the Neutron ml2_confg file. For example, with VXLAN
  networks, the range setting is [ml2_type_vxlan] vni_ranges.
* The :term:`zone` for the `dns_domain` must already exist in Designate and the
  project ID creating the Nova instance, port, or floating IP must have
  permission to create :term:`recordsets<Recordset>` in the :term:`zone`.

These restrictions typically mean that a special network will need to be
created by an administrator that will allow :term:`recordsets<Recordset>` to
be created in Designate.

If these criteria are not all met, Neutron will create a DNS assignment in the
Neutron internal resolvers using the default `dns_domain` specified in the
Neutron configuration file. The current default domain is "openstacklocal.".

.. warning::

   If the user creating the Nova instance, port, or floating IP does not have
   permission to create :term:`recordsets<Recordset>` in the :term:`zone` or
   the :term:`zone` does not exist in Designate, Neutron will create the port
   with the `dns_assignment` field populated using the `dns_domain` provided,
   but no :term:`recordset` will be created in Designate. Neutron will log
   the error "Error publishing port data in external DNS service.".


subnet-dns-publish-fixed-ip
---------------------------

A third Neutron extension is available called `subnet-dns-publish-fixed-ip`.
This extension includes the capabilities of the `dns-domain-ports` extension,
but removes the restrictions if the subnet `dns_publish_fixed_ip` property is
set to True.

dns-integration-domain-keywords
-------------------------------

The fourth Neutron extension, including the capabilities of the
`subnet-dns-publish-fixed-ip` extension, is called
`dns-integration-domain-keywords`. It allows the use of keywords in the
`dns_domain` that will be replaced when a port is created. Valid keywords are:
<project_id>, <project_name>, <user_id>, and <user_name>.

.. note::

   For more information on enabling DNS integration in Neutron, see the
   `Neutron Networking Guide <https://docs.openstack.org/neutron/latest/admin/config-dns-int.html>`_.

DNS for Nova Server Instances
=============================

DNS integration with Neutron allows you to automatically create a DNS
:term:`recordset` for Nova instances. When Nova requests the Neutron port to be
created for the new instance, Neutron will attempt to create a DNS
:term:`recordset` for the port in Designate.

As an example, we will create a new Nova instance with the DNS name of
"server.example.org" registered in Designate.

.. _Neutron criteria: https://docs.openstack.org/neutron/latest/admin/config-dns-int-ext-serv.html#configuration-of-the-externally-accessible-network-for-use-cases-3b-and-3c

.. note::
   This example is for user created networks. DNS records can be automatically
   created for Nova server instances on networks created by a cloud
   administrator if they meet the `Neutron criteria`_.

**Steps**:

1. Check that the `subnet-dns-publish-fixed-ip` Neutron extension is enabled.
2. Create the :term:`zone` "example.org." in Designate.
3. Create a network, providing the `dns_domain` of "example.org.", that we will
   use for the Nova instance.
4. Create a subnet on the network with `dns_publish_fixed_ip` set to True.
5. Create the Nova instance, with name "server" and a NIC on the network.
6. Verify the DNS :term:`recordset` was created in the Designate :term:`zone`.

.. note::

   The DNS domain must always be a :term:`Fully Qualified Domain Name` (FQDN),
   meaning it will always end with a period.

**CLI Commands:**

.. code-block::

   $ openstack extension list --network -f value -c Alias | grep subnet-dns-publish-fixed-ip
   $ openstack zone create --email example@example.org example.org.
   $ openstack network create --dns-domain example.org. example-net
   $ openstack subnet create --allocation-pool start=192.0.2.10,end=192.0.2.200 --network example-net --subnet-range 192.0.2.0/24 --dns-publish-fixed-ip example-subnet
   $ openstack server create --image cirros-0.5.2-x86_64-disk --flavor 1 --nic net-id=example-net server
   $ openstack recordset list --type A example.org.

   +---------------+---------------------+------+------------+--------+--------+
   | id            | name                | type | records    | status | action |
   +---------------+---------------------+------+------------+--------+--------+
   | 7b8d1be6-1b23 | server.example.org. | A    | 192.0.2.44 | ACTIVE | NONE   |
   | -478a-94d5-60 |                     |      |            |        |        |
   | b876dca2c8    |                     |      |            |        |        |
   +---------------+---------------------+------+------------+--------+--------+


DNS for Neutron Ports
=====================

DNS integration with Neutron allows you to automatically create a DNS
:term:`recordset` for Neutron ports.

As an example, we will create a new Neutron port with the DNS name of
"example-port.example.org" registered in Designate.

.. note::
   This example is for user created networks. DNS records can be automatically
   created for Neutron ports on networks created by a cloud administrator if
   they meet the `Neutron criteria`_.

**Steps**:

1. Check that the `subnet-dns-publish-fixed-ip` Neutron extension is enabled.
2. Create the :term:`zone` "example.org." in Designate.
3. Create a network, providing the `dns_domain` of "example.org.", that we will
   use for the Neutron port.
4. Create a subnet on the network with `dns_publish_fixed_ip` set to True.
5. Create the Neutron port specifying the `dns_name` of "example-port" for the
   port.
6. Verify the DNS :term:`recordset` was created in the Designate :term:`zone`.

.. note::

   The DNS domain must always be a :term:`Fully Qualified Domain Name` (FQDN),
   meaning it will always end with a period.

**CLI Commands:**

.. code-block::

   $ openstack extension list --network -f value -c Alias | grep subnet-dns-publish-fixed-ip
   $ openstack zone create --email example@example.org example.org.
   $ openstack network create --dns-domain example.org. example-net
   $ openstack subnet create --allocation-pool start=192.0.2.10,end=192.0.2.200 --network example-net --subnet-range 192.0.2.0/24 --dns-publish-fixed-ip example-subnet
   $ openstack port create --network example-net --dns-name example-port my-example-port
   $ openstack recordset list --type A example.org.

   +---------------+---------------------------+------+-------------+--------+--------+
   | id            | name                      | type | records     | status | action |
   +---------------+---------------------------+------+-------------+--------+--------+
   | 9ebbe94f-2442 | example-port.example.org. | A    | 192.0.2.149 | ACTIVE | NONE  |
   | -4bb8-9cfa-6d |                           |      |             |        |       |
   | ca1daba73f    |                           |      |             |        |       |
   +---------------+---------------------------+------+------------+--------+--------+


DNS for Floating IPs
====================

DNS integration with Neutron allows you to automatically create a DNS
:term:`recordset` for Neutron floating IP addresses.

As an example, we will create a new Neutron floating IP with the DNS name of
"example-fip.example.org" registered in Designate.

**Steps**:

1. Create the Neutron floating IP specifying the `dns_name` of "example-fip"
   and the `dns_domain` as "example.org.".
2. Verify the DNS :term:`recordset` was created in the Designate :term:`zone`.

.. note::

   The DNS domain must always be a :term:`Fully Qualified Domain Name` (FQDN),
   meaning it will always end with a period.

**CLI Commands:**

.. code-block::

   $ openstack floating ip create --dns-name example-fip --dns-domain example.org. example-net
   $ openstack recordset list --type A example.org.

   +---------------+--------------------------+------+-------------+--------+--------+
   | id            | name                     | type | records     | status | action |
   +---------------+--------------------------+------+-------------+--------+--------+
   | e1eca823-169d | example-fip.example.org. | A    | 192.0.2.106 | ACTIVE | NONE  |
   | -4d0a-975e-91 |                          |      |             |        |       |
   | a9907ec0c1    |                          |      |             |        |       |
   +---------------+--------------------------+------+------------+--------+--------+
