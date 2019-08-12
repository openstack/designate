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

Knot DNS 2 Agent backend
************************


Knot DNS 2 User documentation
=============================

This page documents the Agent backend for `Knot DNS <https://www.knot-dns.cz/>`_.

The agent runs on the same host as the resolver. It receives DNS messages from
Mini DNS using private DNS OPCODEs and classes and creates or deletes zones
on Knot using the knotc tool. It also instructs Knot to request AXFR
from MiniDNS when a zone is created or updated.

Support matrix:

* 2.0 and older: not supported
* 2.2.0: `affected by a bug <https://gitlab.labs.nic.cz/labs/knot/issues/460>`_


`Knot DNS documentation <https://www.knot-dns.cz/documentation/>`_

Configuring Knot DNS
--------------------

Assuming Knot has been freshly installed on the system, run as root:

.. code-block:: bash

    # Monitor syslog during the next steps
    tail -f /var/log/syslog

    # Start the daemon, ensure it's running
    service knot start
    netstat -npltu | grep knotd

    # Create the config database
    knotc conf-init

    # Edit /etc/default/knot
    # Set the variable:
    # KNOTD_ARGS="-C /var/lib/knot/confdb"

    # Restart
    service knot restart

    # Check if the deamon is still running from the conf file in /etc/knot/
    ps axuw | grep knotd

    # if so, apply this workaround for bug
    # https://gitlab.labs.nic.cz/labs/knot/issues/455
    ( cd /etc/default/ && ln -s knot knotd )
    service knot restart
    ps axuw | grep knotd

    # Ensure the confdb is present
    test -f /var/lib/knot/confdb/data.mdb && echo OK

    # Create the configuration
    # Populate the variable with the MiniDNS ipaddr:
    MINIDNS_IPADDR=

    knotc conf-begin
    knotc conf-set server.listen 0.0.0.0@53
    # To listen on IPv6 as well, also run this:
    # knotc conf-set server.listen '::@53'
    knotc conf-set remote[minidns]
    knotc conf-set remote[minidns].address $MINIDNS_IPADDR@5354
    knotc conf-set template[default]
    knotc conf-set template[default].master minidns
    knotc conf-set template[default].acl acl_minidns
    knotc conf-set template[default].semantic-checks on
    knotc conf-set zone[example.com]
    knotc conf-set log.any info
    knotc conf-set log.target syslog
    knotc conf-set acl[acl_minidns]
    knotc conf-set acl[acl_minidns].address $MINIDNS_IPADDR
    knotc conf-set acl[acl_minidns].action notify
    # Review the changes and commit
    knotc conf-diff
    knotc conf-commit

    # Optionally check and back up the conf
    knotc conf-check
    knotc conf-export knot.conf.bak && cat knot.conf.bak

    # Ensure the zone survives a restart
    service knot restart
    knotc zone-status example.com

    # Test Knot: this should return the version
    dig @127.0.0.1 version.server CH TXT

If needed, create a rootwrap filter, as root:

.. code-block:: bash

    cat > /etc/designate/rootwrap.d/knot2.filters <<EOF
    # cmd-name: filter-name, raw-command, user, args
    [Filters]
    knotc: CommandFilter, /usr/sbin/knotc, root
    EOF

    # Check the filter:
    sudo /usr/local/bin/designate-rootwrap /etc/designate/rootwrap.conf knotc status

Configure the "service.agent" and "backend.agent.knot2" sections
in /etc/designate/designate.conf

Look in designate.conf.example for examples

Create an agent pool:

.. code-block:: bash

    # Fetch the existing pool(s) if needed or start from scratch
    designate-manage pool generate_file --file /tmp/pool.yaml
    # Edit the file (see below) and reload it as:
    designate-manage pool update --file /tmp/pool.yaml

The "targets" section in pool.yaml should look like:

.. code-block:: ini

  targets:
  - description: knot2 agent
    masters:
    - host: <MiniDNS IP addr>
      port: 5354
    options: {}
    options:
    - host: <Agent IP addr>
      port: 5358
    type: agent

Developer documentation
=======================

Devstack testbed
----------------

Follow "Setting up Knot DNS on Ubuntu Trusty"

Configure Knot to slave from MiniDNS on 192.168.121.131

Knotd configuration example (sudo knotc conf-export <filename>):

.. code-block:: yaml

    # Configuration export (Knot DNS 2.1.1)

    server:
        listen: "0.0.0.0@53"

    log:
    - target: "syslog"
        any: "debug"

    acl:
    - id: "acl_minidns"
        address: [ "192.168.121.131" ]
        action: [ "notify" ]

    remote:
    - id: "minidns"
        address: "192.168.121.131@5354"

    template:
    - id: "default"
        master: "minidns"
        acl: "acl_minidns"
        semantic-checks: "on"
