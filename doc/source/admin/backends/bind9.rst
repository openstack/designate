..
    Copyright 2013 Hewlett-Packard Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. _bind9_backend_docs:

Bind9 Backend
=============

This page documents using the Bind 9 backend.
The backend uses the rndc utility to create and delete zones remotely.

The traffic between rndc and Bind is authenticated with a key.

.. _bind9_target_example:

Designate Configuration
-----------------------

Example configuration required for Bind9 operation.
One section for each pool target

   .. literalinclude:: sample_yaml_snippets/bind.yaml
       :language: yaml

The key and config files are relative to the host running Designate
(and can be different from the hosts running Bind)

Then update the pools in designate - see :ref:`designate_manage_pool`
for further details on the ``designate-manage pool`` command

.. code-block:: console

    $ designate-manage pool update

Bind9 Configuration
-------------------

Ensure Bind can access the /etc/bind/rndc.conf and /etc/bind/rndc.key files and
receive rndc traffic from Designate.

Enable rndc addzone/delzone functionality by editing named.conf.options
or named.conf and add this line under options

.. code-block:: c

    allow-new-zones yes;

Example configuration of /etc/bind/rndc.key

.. code-block:: c

    key "rndc-key" {
        algorithm hmac-md5;
        secret "<b64-encoded string>";
    };
