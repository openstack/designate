..
    Copyright 2016 Hewlett Packard Enterprise Development Company LP

    Author: Federico Ceratto <federico.ceratto@hpe.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

gdnsd Agent backend
*******************


User documentation
==================

This page documents the Agent backend for `gdnsd <http://gdnsd.org/>`_.

The agent runs on the same host as the resolver. It receives DNS messages
from Mini DNS using private DNS OPCODEs and classes and
creates/updates/deletes zones on gdnsd using zone files under
the gdnsd configuration directory.

The backend supports gdnsd from version 2.0

`gdnsd documentation <https://github.com/gdnsd/gdnsd/wiki>`_

Setting up gdnsd on Ubuntu Vivid
--------------------------------

Run as root:

.. code-block:: bash

    apt-get update
    apt-get install gdnsd

Configuring gdnsd
-----------------

Assuming gdnsd has been freshly installed on the system, run as root:

.. code-block:: bash

    # Monitor syslog during the next steps
    tail -f /var/log/syslog

    # config check should be successful
    /usr/sbin/gdnsd checkconf

    # Start the daemon if needed
    service gdnsd status
    service gdnsd start

    # gdnsd should be listening on TCP and UDP ports
    netstat -lnptu | grep '/gdnsd'

    # Test the daemon: it should respond with "gdnsd"
    dig @127.0.0.1 CH TXT +short

Configure the "service.agent" and "backend.agent.gdnsd" sections
in /etc/designate/designate.conf

Look in designate.conf.example for more complete examples

.. code-block:: ini

    [service:agent]
    backend_driver = gdnsd
    # Place here the MiniDNS ipaddr and port (not the agent itself)
    masters = 192.168.27.100:5354

    [backend:agent:gdnsd]
    #gdnsd_cmd_name = gdnsd
    #confdir_path = /etc/gdnsd
    #query_destination = 127.0.0.1

Ensure that the "zones" directory under "confdir_path" (default /etc/gdnsd)
is readable and writable by the system user running the Designate Agent

Create an agent pool:

.. code-block:: bash

    # Fetch the existing pool(s) if needed
    designate-manage pool generate_file --file /tmp/pool.yaml
    # Edit the file (see below) and reload it as:
    designate-manage pool update --file /tmp/pool.yaml

The "targets" section in pool.yaml should look like:

.. code-block:: ini

  targets:
  - description: gdnsd agent
    masters:
    - host: <MiniDNS IP addr>
      port: 5354
    options: {}
    options:
    - host: <Agent IP addr>
      port: 5358
    type: agent

Start the Designate Agent. You should see log messages similar to:

.. code-block:: bash

    2016-05-03 15:13:38.193 INFO designate.backend.agent_backend.impl_gdnsd [-] gdnsd command: 'gdnsd'
    2016-05-03 15:13:38.193 INFO designate.backend.agent_backend.impl_gdnsd [-] gdnsd conf directory: '/etc/gdnsd'
    2016-05-03 15:13:38.194 INFO designate.backend.agent_backend.impl_gdnsd [-] Resolvers: ['127.0.0.1']

