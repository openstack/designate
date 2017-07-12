Prerequisites
-------------

Before you install and configure the DNS service,
you must create service credentials and API endpoints.

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ source admin-openrc

#. To create the service credentials, complete these steps:

   * Create the ``designate`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt designate

   * Add the ``admin`` role to the ``designate`` user:

     .. code-block:: console

        $ openstack role add --project service --user designate admin

   * Create the designate service entities:

     .. code-block:: console

        $ openstack service create --name designate --description "DNS" dns

#. Create the DNS service API endpoint:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        dns public http://controller:9001/
