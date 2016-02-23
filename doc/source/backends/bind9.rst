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

Bind9 Backend
=============

This page documents using the Pool Manager Bind 9 backend.
The backend uses the rndc utility to create and delete zones remotely.

The traffic between rndc and Bind is authenticated with a key.

Designate Configuration
-----------------------

Example configuration required for Bind9 operation. One section for each pool target

.. code-block:: ini

    [pool_target:f26e0b32-736f-4f0a-831b-039a415c481e]
    options = rndc_host: 192.168.27.100, rndc_port: 953, rndc_config_file: /etc/bind/rndc.conf, rndc_key_file: /etc/bind/rndc.key, port: 53, host: 192.168.27.100, clean_zonefile: false
    masters = 192.168.27.100:5354
    type = bind9

The key and config files are relative to the host running Pool Manager (and can
be different from the hosts running Bind)

Bind9 Configuration
-------------------

Ensure Bind can access the /etc/bind/rndc.conf and /etc/bind/rndc.key files and
receive rndc traffic from Pool Manager.

Enable rndc addzone/delzone functionality by editing named.conf.options or named.conf and add this line under options

.. code-block:: c

    allow-new-zones yes;

Example configuration of /etc/bind/rndc.key

.. code-block:: c

    key "rndc-key" {
        algorithm hmac-md5;
        secret "<b64-encoded string>";
    };
