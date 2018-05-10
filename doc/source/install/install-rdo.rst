.. _install-rdo:

Install and configure for Red Hat Enterprise Linux and CentOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to install and configure the DNS
service for Red Hat Enterprise Linux 7 and CentOS 7.

.. include:: common_prerequisites.rst

Install and configure components
--------------------------------

.. note::

   Default configuration files vary by distribution. You might need
   to add these sections and options rather than modifying existing
   sections and options. Also, an ellipsis (``...``) in the configuration
   snippets indicates potential default configuration options that you
   should retain.

#. Install the packages:

   .. code-block:: console

      # yum install openstack-designate\*

#. Create a ``designate`` database that is accessible by the ``designate``
   user. Replace ``DESIGNATE_DBPASS`` with a suitable password:

   .. code-block:: console

      # mysql -u root -p
      MariaDB [(none)]> CREATE DATABASE designate CHARACTER SET utf8 COLLATE utf8_general_ci;
      MariaDB [(none)]> GRANT ALL PRIVILEGES ON designate.* TO 'designate'@'localhost' \
      IDENTIFIED BY 'DESIGNATE_DBPASS';
      MariaDB [(none)]> GRANT ALL PRIVILEGES ON designate.* TO 'designate'@'%' \
      IDENTIFIED BY 'DESIGNATE_DBPASS';

#. Install the BIND packages:

   .. code-block:: console

      # yum install bind bind-utils

#. Add the following options in the ``/etc/named.conf`` file::

      options {
          ...
          allow-new-zones yes;
          request-ixfr no;
          listen-on port 53 { 127.0.0.1; };
          recursion no;
          allow-query { 127.0.0.1; };
      };

#. Create an RNDC Key:

   .. code-block:: console

      # rndc-confgen -a -k designate -c /etc/designate/rndc.key -r /dev/urandom

#. Add the key to ``/etc/named.conf``::

      ...
      include "/etc/designate/rndc.key";

      controls {
        inet 127.0.0.1 port 953
          allow { 127.0.0.1; } keys { "designate"; };
      };


#. Start the DNS service and configure it to start when the system boots:

   .. code-block:: console

      # systemctl enable named

      # systemctl start named

#. Edit the ``/etc/designate/designate.conf`` file and
   complete the following actions:

   * In the ``[service:api]`` section, configure ``auth_strategy``:

     .. code-block:: ini

        [service:api]
        listen = 0.0.0.0:9001
        auth_strategy = keystone
        api_base_uri = http://controller:9001/
        enable_api_v2 = True
        enabled_extensions_v2 = quotas, reports

   * In the ``[keystone_authtoken]`` section, configure the following options:

     .. code-block:: ini

        [keystone_authtoken]
        auth_type = password
        username = designate
        password = DESIGNATE_PASS
        project_name = service
        project_domain_name = Default
        user_domain_name = Default
        www_authenticate_uri = http://controller:5000/
        auth_url = http://controller:5000/

     Replace ``DESIGNATE_PASS`` with the password you chose for the
     ``designate`` user in the Identity service.

   * In the ``[service:worker]`` section, enable the worker model:

     .. code-block:: ini

        enabled = True
        notify = True

   * In the ``[storage:sqlalchemy]`` section, configure database access:

     .. code-block:: ini

        [storage:sqlalchemy]
        connection = mysql+pymysql://designate:DESIGNATE_DBPASS@controller/designate

     Replace ``DESIGNATE_DBPASS`` with the password you chose for the
     ``designate`` database.

   * Populate the designate database

     .. code-block:: console

        # su -s /bin/sh -c "designate-manage database sync" designate

#. Start the designate central and API services and configure them
   to start when the system boots:

   .. code-block:: console

      # systemctl enable designate-central designate-api

      # systemctl start designate-central designate-api

#. Create a pools.yaml file in ``/etc/designate/pools.yaml`` with the following
   contents:

   .. code-block:: yaml

      - name: default
        # The name is immutable. There will be no option to change the name after
        # creation and the only way will to change it will be to delete it
        # (and all zones associated with it) and recreate it.
        description: Default Pool

        attributes: {}

        # List out the NS records for zones hosted within this pool
        # This should be a record that is created outside of designate, that
        # points to the public IP of the controller node.
        ns_records:
          - hostname: ns1-1.example.org.
            priority: 1

        # List out the nameservers for this pool. These are the actual BIND servers.
        # We use these to verify changes have propagated to all nameservers.
        nameservers:
          - host: 127.0.0.1
            port: 53

        # List out the targets for this pool. For BIND there will be one
        # entry for each BIND server, as we have to run rndc command on each server
        targets:
          - type: bind9
            description: BIND9 Server 1

            # List out the designate-mdns servers from which BIND servers should
            # request zone transfers (AXFRs) from.
            # This should be the IP of the controller node.
            # If you have multiple controllers you can add multiple masters
            # by running designate-mdns on them, and adding them here.
            masters:
              - host: 127.0.0.1
                port: 5354

            # BIND Configuration options
            options:
              host: 127.0.0.1
              port: 53
              rndc_host: 127.0.0.1
              rndc_port: 953
              rndc_key_file: /etc/designate/rndc.key

#. Update the pools:

   .. code-block:: console

        # su -s /bin/sh -c "designate-manage pool update" designate

#. Start the designate and mDNS services and configure them to start when the
   system boots:

   .. code-block:: console

      # systemctl enable designate-worker designate-producer designate-mdns

      # systemctl start designate-worker designate-producer designate-mdns
