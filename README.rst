========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/designate.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

===================
OpenStack Designate
===================

Designate is an OpenStack project, providing DNSaaS.

IRC: #openstack-dns @ oftc

Installation: https://docs.openstack.org/designate/latest/

API
---

To learn how to use Designate's API, consult the documentation available
online at:

- `DNS API Reference <https://docs.openstack.org/api-ref/dns/>`__

For more information on OpenStack APIs, SDKs and CLIs in general, refer to:

- `OpenStack for App Developers <https://www.openstack.org/appdev/>`__
- `Development resources for OpenStack clouds
  <https://developer.openstack.org/>`__

Development
===========

Designate follows the `OpenStack Gerrit Workflow`_

Setup
-----

Setup a working environment:

.. code-block:: bash

    git clone https://opendev.org/openstack/designate
    cd designate
    virtualenv .venv
    . .venv/bin/activate
    pip install -r requirements.txt -r test-requirements.txt
    pip install -e .

Building Docs
-------------

To build the documentation from the restructured text source, do the following:

.. code-block:: bash

    tox -e docs

Now point your browser at doc/build/html/index.html
(the official documentation is published to `docs.openstack.org`_  by the
maintainers.

Testing
-------

Execute all unit tests

.. code-block:: shell

    tox -e py3

Execute only backend tests

.. code-block:: shell

    tox -e py3 -- unit.backend

Execute only a single test

.. code-block:: shell

    tox -e py3 -- unit.backend.test_pdns4.PDNS4BackendTestCase.test_create_zone_success

Contributing
------------
Install the git-review package to make life easier

.. code-block:: shell

    pip install git-review


Branch, work, & submit:

.. code-block:: shell

    # cut a new branch, tracking master
    git checkout --track -b bug/id origin/master
    # work work work
    git add stuff
    git commit
    # rebase/squash to a single commit before submitting
    git rebase -i
    # submit
    git-review

Other Information
-----------------

* Free software: Apache license
* Documentation: https://docs.openstack.org/designate/latest/
* Release notes: https://docs.openstack.org/releasenotes/designate/
* Source: https://opendev.org/openstack/designate
* Bugs: https://bugs.launchpad.net/designate
* Blueprints: https://blueprints.launchpad.net/designate


.. _OpenStack Gerrit Workflow: https://docs.openstack.org/infra/manual/developers.html#development-workflow
.. _docs.openstack.org: https://docs.openstack.org/designate/latest/
