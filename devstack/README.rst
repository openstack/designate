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

   **Note:** Running with a multipool option:
   Perform the above step, and in addition set the backend driver and
   scheduler filters::

    SCHEDULER_FILTERS=attribute,pool_id_attributes,in_doubt_default_pool
    DESIGNATE_BACKEND_DRIVER=multipool-bind9

3. run ``stack.sh``
