.. _verify:

Verify operation
~~~~~~~~~~~~~~~~

Verify operation of the DNS service.

.. note::

   Perform these commands on the controller node.

#. Source the ``admin`` tenant credentials:

   .. code-block:: console

      $ . admin-openrc

#. List service components to verify successful launch and
   registration of each process:

   .. code-block:: console

      $ ps -aux | grep designate

      ../usr/bin/python /usr/bin/designate-mdns --config-file /etc/designate/designate.conf
      ../usr/bin/python /usr/bin/designate-central --config-file /etc/designate/designate.conf
      ../usr/bin/python /usr/bin/designate-api --config-file /etc/designate/designate.conf
      ../usr/bin/python /usr/bin/designate-worker --config-file /etc/designate/designate.conf
      ../usr/bin/python /usr/bin/designate-producer --config-file /etc/designate/designate.conf

      $ openstack dns service list
      +--------------------------------------+--------------------------+--------------+--------+-------+--------------+
      | id                                   | hostname                 | service_name | status | stats | capabilities |
      +--------------------------------------+--------------------------+--------------+--------+-------+--------------+
      | 918a8f6e-9e7e-453e-8583-cbefa7ae7f8f | vagrant-ubuntu-trusty-64 | central      | UP     | -     | -            |
      | 982f78d5-525a-4c36-af26-a09aa39de5d7 | vagrant-ubuntu-trusty-64 | api          | UP     | -     | -            |
      | eda2dc16-ad27-4ee1-b091-bb75b6ceaffe | vagrant-ubuntu-trusty-64 | mdns         | UP     | -     | -            |
      | 00c5c372-e630-49b1-a6b6-17e3fa4544ea | vagrant-ubuntu-trusty-64 | worker       | UP     | -     | -            |
      | 8cdaf2e9-accd-4665-8e9e-be26f1ccfe4a | vagrant-ubuntu-trusty-64 | producer     | UP     | -     | -            |
      +--------------------------------------+--------------------------+--------------+--------+-------+--------------+

   .. note::

      This output should indicate at least one of each of the ``central``,
      ``api``, ``producer``, ``mdns`` and ``worker`` components
      on the controller node.

      This output may differ slightly depending on the distribution.
