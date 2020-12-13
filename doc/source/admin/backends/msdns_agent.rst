..
    Copyright 2016 Cloudbase Solutions Srl

    Author: Alin Balutoiu <abalutoiu@cloudbasesolutions.com>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

MSDNS Agent Backend
*******************

MSDNS User Documentation
========================

This page documents using the MSDNS Agent backend.

The agent runs on the Windows host where the Microsoft DNS Server feature
is installed. It receives DNS messages from Mini DNS using private
DNS OPCODEs and classes and creates or deletes zones using WMI calls.

It also instructs MSDNS to request AXFR from MiniDNS when a zone is created
or updated.

`Microsoft DNS documentation for managing DNS zones
<https://msdn.microsoft.com/en-us/library/windows/desktop/ms682757.aspx>`_

Setting up the Microsoft DNS server on Windows Server
-----------------------------------------------------

The DNS Server role can be installed on the system by following the
documentation available here:
`How to install the DNS Server role
<https://technet.microsoft.com/en-us/library/cc725925.aspx>`_

Configuring MSDNS
-----------------

Assuming the DNS Server role has been installed on the system, follow the
next steps to complete the configuration.

These steps are for the Windows host which will run the designate agent.
Make sure that Python 2.7 or Python 3.4 is installed on the system already.

To install Designate, clone the repository from https://github.com/openstack/designate
and do a pip install. Example:

.. code-block:: console

    git clone https://github.com/openstack/designate
    pip install .\\designate

After that, we need to configure the Designate Agent.
Inside the github repository, there is a folder named "etc/designate"
which can be used as default configuration.

Copy the folder somewhere else, for this example we will copy it to
C:\\etc\\designate
Inside the configuration folder, make a copy of designate.conf.sample
and rename the copy to designate.conf
Example:

.. code-block:: console

    copy C:\\etc\\designate\\designate.conf.sample C:\\etc\\designate\\designate.conf


Configure the "service.agent" and "backend.agent.msdns" sections in
C:\\etc\\designate\\designate.conf

Look in C:\\etc\\designate\\designate.conf.example for more complete examples.

.. code-block:: ini

    [service:agent]
    backend_driver = msdns
    # Place here the MiniDNS ipaddr and port (no the agent itself)
    masters = <MiniDNS IP addr>:53

Ensure that "policy_file" under the [default] section is set:

.. code-block:: ini

    policy_file = C:\\etc\\designate\\policy.yaml

Start the designate agent using
(Python 2.7 was installed in the default location C:\\Python27):

.. code-block:: console

    C:\\Python27\\Scripts\\designate-agent.exe --config-file 'C:\\etc\\designate\\designate.conf'

You should see log messages similar to:

.. code-block:: console

    2016-06-22 02:00:47.177 3436 INFO designate.backend.agent_backend.impl_msdns [-] Started msdns backend
    2016-06-22 02:00:47.177 3436 INFO designate.service [-] _handle_tcp thread started
    2016-06-22 02:00:47.177 3436 INFO designate.service [-] _handle_udp thread started


The following steps are for the system running the Designate controller.

Make sure to set the mDNS port to 53 in the ``[service:mdns]`` section.
MS DNS does not support Masters that are on any port other than 53.

Create an agent pool:

.. code-block:: bash

    # Fetch the existing pool(s) if needed or start from scratch
    designate-manage pool generate_file --file /tmp/pool.yaml
    # Edit the file (see below) and reload it as:
    designate-manage pool update --file /tmp/pool.yaml

The "targets" section in pool.yaml should look like:

.. code-block:: ini

    targets:
    - description: Microsoft DNS agent
      masters:
      - host: <MiniDNS IP addr>
        port: 53
      options: {}
      options:
      - host: <Agent IP addr>
        port: 5358
      type: agent
