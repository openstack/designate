..
    Copyright 2021 NS1 inc. https://www.ns1.com

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _backend-ns1:

NS1 Backend
===========

NS1 Configuration
-----------------


1. Configure the NS1 Backend using this sample target snippet

.. literalinclude:: sample_yaml_snippets/ns1.yaml
   :language: yaml

2. Then update the pools in designate

.. code-block:: console

    $ designate-manage pool update

See :ref:`designate_manage_pool` for further details on
the ``designate-manage pool`` command, and :ref:`pools`
for information about the yaml file syntax


TSIG Key Configuration
----------------------

In some cases a deployer may need to use tsig keys to sign AXFR (zone transfer)
requests. As NS1 does not support a per host key setup, this needs to be set
on a per zone basis, on creation.

To do this, generate a tsigkey using any of available utilities
(e.g. tsig-keygen):

.. code-block:: bash

    $ tsig-keygen -a hmac-sha512 testkey
    key "testkey" {
        algorithm hmac-sha512;
        secret "vQbMI3u5QGUyRu6FWRm16eL0F0dfOOmVJjWKCTg4mIMNnba0g2PLrV+0G92WcTfJrgqZ20a4hv3RWDICKCcJhw==";
    };

Then insert it into Designate. Make sure the pool id is correct
(the ``--resource-id`` below.)

.. code-block:: bash

    openstack tsigkey create --name testkey --algorithm hmac-sha512 --secret 4EJz00m4ZWe005HjLiXRedJbSnCUx5Dt+4wVYsBweG5HKAV6cqSVJ/oem/6mLgDNFAlLP3Jg0npbg1SkP7RMDg== --scope POOL --resource-id 794ccc2c-d751-44fe-b57f-8894c9f5c842

Then add it to the ``pools.yaml`` file as shown in the example.
