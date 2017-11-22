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

Djbdns Agent backend
********************


Djbdns User documentation
=========================

This page documents the Agent backend for `djbdns <https://cr.yp.to/djbdns.html>`_.

The agent runs on the same host as the `tinydns <https://cr.yp.to/djbdns/tinydns.html>`_ resolver.
It receives DNS messages from Mini DNS using private DNS OPCODEs
and classes and creates or deletes zones in the data.cdb file using
`axfr-get <https://cr.yp.to/djbdns/axfr-get.html>`_ and
`tinydns-data <https://cr.yp.to/djbdns/tinydns-data.html>`_

Setting up Djbdns on Ubuntu Trusty
------------------------------------

Assuming no DNS resolver is already installed, run as root:

.. code-block:: bash

    set -u
    datadir=/var/lib/djbdns
    ug_name=djbdns
    tinydns_ipaddr=127.0.0.1

    [[ -d $datadir ]] && echo "$datadir already exists" && exit 1
    set -e
    apt-get update
    apt-get install dbndns daemontools
    if ! getent passwd $ug_name >/dev/null; then
      adduser --quiet --system --group --no-create-home --home /nonexistent $ug_name
    fi
    tinydns-conf $ug_name $ug_name $datadir $tinydns_ipaddr
    cd $datadir/root
    tinydns-data data
    chown -Rv $ug_name:$ug_name $datadir

Setup the a Systemd service or, alternatively, an initfile to start TinyDNS.

In the contrib/djbdns directory there are example files for both.

.. code-block:: bash

    systemctl daemon-reload
    service tinydns start
    service tinydns status


If needed, create the rootwrap filters, as root:

.. code-block:: bash

    cat > /etc/designate/rootwrap.d/djbdns.filters <<EOF
    # cmd-name: filter-name, raw-command, user, args
    [Filters]
    tcpclient: CommandFilter, /usr/bin/tcpclient, root
    axfr-get: CommandFilter, /usr/bin/axfr-get, root
    EOF

    # Check the filter:
    sudo /usr/local/bin/designate-rootwrap /etc/designate/rootwrap.conf tcpclient -h
    sudo /usr/local/bin/designate-rootwrap /etc/designate/rootwrap.conf axfr-get -h

Configure the "service.agent" and "backend.agent.djbdns"
sections in /etc/designate/designate.conf

Look in designate.conf.example for examples.

Create an agent pool:

.. code-block:: bash

    # Fetch the existing pool(s) if needed or start from scratch
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


Testing
^^^^^^^

Create new zones and records. Monitor the agent logfile and the contents of the
TinyDNS datadir. The data.cdb file should be receiving updates.

.. code-block:: bash

    openstack zone create --email example@example.org example.org.
    openstack recordset create example.org. --type A foo --records 1.2.3.4
    dig example.org @<tinydns_ipaddr> SOA
    dig foo.example.org @<tinydns_ipaddr> A

Developer documentation
=======================

Devstack testbed
----------------

Follow "Setting up Djbdns on Ubuntu Trusty"

Configure Tinydns to do AXFR from MiniDNS on 192.168.121.131
