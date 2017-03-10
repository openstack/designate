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
      MariaDB [(none)]> CREATE DATABASE designate;
      MariaDB [(none)]> GRANT ALL PRIVILEGES ON designate.* TO 'designate'@'localhost' \
      IDENTIFIED BY 'DESIGNATE_DBPASS';

#. Install the BIND packages:

   .. code-block:: console

      # yum install bind

#. Add the following options in the ``/etc/named.conf`` file:

   .. code-block:: none

      options {
          ...
          allow-new-zones yes;
          request-ixfr no;
          recursion no;
      };

#. Create an RNDC Key:

   .. code-block:: console

      # rndc-confgen -a -k designate -c /etc/designate/rndc.key -r /dev/urandom

#. Add the key to ``/etc/named.conf``:

   .. code-block:: none

      ...
      # This should be the contents of ``/etc/designate/rndc.key``
      key "designate" {
        algorithm hmac-md5;
        secret "OAkHNQy0m6UPcv55fiVAPw==";
      };
      # End of content from ``/etc/designate/rndc.key``

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
        api_host = 0.0.0.0
        api_port = 9001
        auth_strategy = keystone
        enable_api_v1 = True
        enabled_extensions_v1 = quotas, reports
        enable_api_v2 = True

   * In the ``[keystone_authtoken]`` section, configure the following options:

     .. code-block:: ini

        [keystone_authtoken]
        auth_host = controller
        auth_port = 35357
        auth_protocol = http
        admin_tenant_name = service
        admin_user = designate
        admin_password = DESIGNATE_PASS

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

#. Start the designate central and API services and configure them to start when
   the system boots:

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
          - type: bind
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
