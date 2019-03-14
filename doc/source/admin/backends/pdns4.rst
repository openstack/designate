..
    Copyright 2016 Hewlett Packard Enterprise Development, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _backend-pdns4:

PDNS4 Backend
=============

PDNS4 Configuration
-------------------

The version PowerDNS in Ubuntu Xenial is pdns4.
This has a different DB schema, and is incompatible with the legacy PowerDNS
driver. In PDNS 4 the API was marked stable, and this is what we will use.

You will need to configure PowerDNS, and its database before performing these
steps.

You will need to use a database backend for PowerDNS's API to function.

See `PowerDNS Docs`_ for details.

1. Enable the API in the ``pdns.conf`` file.

.. code-block:: ini

    webserver=yes
    api=yes
    api-key=changeme

2. Configure the PowerDNS Backend using this sample target snippet

.. literalinclude:: sample_yaml_snippets/pdns4.yaml
   :language: yaml

3. Then update the pools in designate

.. code-block:: console

    $ designate-manage pool update

See :ref:`designate_manage_pool` for further details on
the ``designate-manage pool`` command, and :ref:`pools`
for information about the yaml file syntax


TSIG Key Configuration
----------------------

.. note:: This is only available in PowerDNS 4.2 or newer

In some cases a deployer may need to use tsig keys to sign AXFR (zone transfer)
requests. As pdns does not support a per host key setup, this needs to be set
on a per zone basis, on creation.

To do this, generate a tsigkey on the PowerDNS Server:

.. code-block:: bash

    $ pdnsutil generate-tsig-key <keyname> hmac-sha512
    Create new TSIG key keyname hmac-sha512 4EJz00m4ZWe005HjLiXRedJbSnCUx5Dt+4wVYsBweG5HKAV6cqSVJ/oem/6mLgDNFAlLP3Jg0npbg1SkP7RMDg==

Then insert it into Designate. Make sure the pool id is correct
(the ``--resource-id`` below.)

.. code-block:: bash

    openstack tsigkey create --name <keyname> --algorithm hmac-sha512 --secret 4EJz00m4ZWe005HjLiXRedJbSnCUx5Dt+4wVYsBweG5HKAV6cqSVJ/oem/6mLgDNFAlLP3Jg0npbg1SkP7RMDg== --scope POOL --resource-id 794ccc2c-d751-44fe-b57f-8894c9f5c842

Then add it to the ``pools.yaml`` file as shown in the example. The ID used is
the name of the key in the PowerDNS server.

.. _PowerDNS Docs: https://doc.powerdns.com/md/authoritative/installation/
