.. _tempest:

===============
 Tempest tests
===============

The Tempest tests are functional tests that hit a live Designate endpoint and
verify responses.

Installation
============

The tests depend on both ``tempest-lib`` and ``tempest``:

::

    # install tempest
    git clone https://github.com/openstack/tempest.git
    pip install tempest/

    # tempest-lib is in test-requirements.txt
    cd designate
    pip install -r requirements.txt -r test-requirements.txt
    python setup.py develop

Configuration
=============

The Tempest tests look for the file ``functionaltests/designate-tempest.conf``,
which contains information about your Keystone setup. For the time being, these
tests require Keystone.

::

    [identity]
    # Replace these with values that represent your identity configuration
    uri=http://localhost:5000/v2.0
    uri_v3=http://localhost:5000/v3
    auth_version=v2
    region=RegionOne

    username=admin
    tenant_name=admin
    password=password
    domain_name=Default

    admin_username=admin
    admin_tenant_name=admin
    admin_password=password
    admin_domain_name=Default


Execution
=========

The tests should work with any test runner, like ``nose``:

::

    cd functionaltests
    pip install nose
    nosetests --logging-level=WARN api/

A file ``.testr.conf`` is included for use with ``testr``:

::

    cd functionaltests
    pip install testrepository
    testr init
    testr run
