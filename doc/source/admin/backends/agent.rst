..
    Copyright 2016 Hewlett Packard Enterprise Development Company LP

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

Agent Backend
=============

This page documents using the various Agent backends, and it's accompanying
service, `designate-agent`. This backend uses an extension of the DNS protocol
itself to send management requests to the remote agent processes, where the
requests will be actioned.

The `rpc` traffic between designate and the `agent` is both unauthenticated and
unencrypted. Do not run this traffic over unsecured networks.

Designate Configuration
-----------------------

For each designate-agent running, add a target to the pools.yaml configuration
file, using the following template:

   .. literalinclude:: sample_yaml_snippets/agent.yaml
       :language: yaml

Then update the designate pools database using the ``designate-manage pool``
command - see :ref:`designate_manage_pool` for further details on the
``designate-manage pool`` command:

.. code-block:: console

    $ designate-manage pool update

.. TODO: Document how to configure the agent service itself, and the available
   agent backends.
