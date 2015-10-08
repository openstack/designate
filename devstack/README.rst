====================
Enabling in Devstack
====================

1. Download DevStack::

    git clone https://git.openstack.org/openstack-dev/devstack.git
    cd devstack

2. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin designate https://git.openstack.org/openstack/designate

3. run ``stack.sh``
