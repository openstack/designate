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

      $ openstack dns service list
      +--------------------------------------+--------------------------+--------------+--------+-------+--------------+
      | id                                   | hostname                 | service_name | status | stats | capabilities |
      +--------------------------------------+--------------------------+--------------+--------+-------+--------------+
      | 14283849-ff64-4467-9cbb-d9050ffa08c0 | vagrant-ubuntu-trusty-64 | central      | UP     | -     | -            |
      | eb7d938f-5b24-4c9b-b4f7-05b9a8ea45f2 | vagrant-ubuntu-trusty-64 | api          | UP     | -     | -            |
      | 5dca293e-5fa2-4a3d-b486-4debad920da3 | vagrant-ubuntu-trusty-64 | zone_manager | UP     | -     | -            |
      | 487e7215-6f61-495d-87b3-86be09406750 | vagrant-ubuntu-trusty-64 | mdns         | UP     | -     | -            |
      | 6b1d1de6-c820-4843-993b-663fca73f905 | vagrant-ubuntu-trusty-64 | pool_manager | UP     | -     | -            |
      +--------------------------------------+--------------------------+--------------+--------+-------+--------------+

   .. note::

      This output should indicate at least one of each of the ``central``,
      ``api``, ``zone_manager``, ``mdns`` and ``pool_manager`` components
      on the controller node.

      This output may differ slightly depending on the distribution.
