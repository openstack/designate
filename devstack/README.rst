====================
Enabling in Devstack
====================

**WARNING**: the stack.sh script must be run in a disposable VM that is not
being created automatically, see the README.md file in the "devstack"
repository.  See contrib/vagrant to create a vagrant VM.

1. Download DevStack::

    git clone https://opendev.org/openstack/devstack.git
    cd devstack

2. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin designate https://opendev.org/openstack/designate

   **Note:** Running with a multipool or split-horizon option:
   Perform the above step, and in addition set the backend driver and
   scheduler filters::

    SCHEDULER_FILTERS=attribute,pool_id_attribute,in_doubt_default_pool

   For multipool (two separate BIND instances)::

    DESIGNATE_BACKEND_DRIVER=multipool-bind9

   For split-horizon (two BIND instances with TSIG-based views)::

    DESIGNATE_BACKEND_DRIVER=split-horizon-bind9

3. run ``stack.sh``
