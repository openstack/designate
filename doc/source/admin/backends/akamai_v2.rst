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

.. _akamai_v2_backend_docs:

Akamai v2 Backend
=================

This page documents using the Akamai v2 backend.
The backend uses the FastDNS V2 API to create and delete zones remotely.

Designate Configuration
-----------------------

Example configuration required:
One section for each pool target

   .. literalinclude:: sample_yaml_snippets/akamai-v2.yaml
       :language: yaml


Then update the pools in designate - see :ref:`designate_manage_pool`
for further details on the ``designate-manage pool`` command

.. code-block:: console

    $ designate-manage pool update

