================
Getting Involved
================

.. toctree::
    :maxdepth: 1

    devstack

#openstack-dns IRC channel
--------------------------

There is an active IRC channel at irc://oftc.net/#openstack-dns,
where many of the designate contributors can be found, as
well as users from various organisations.

Contributing
------------

For general information on contributing to OpenStack please see the
`contributor guide <https://docs.openstack.org/contributors/>`_ to get
started. It covers all the basics that are common to all OpenStack
projects: the accounts you need, the basics of interacting with our
Gerrit review system, how we communicate as a community, etc.

We welcome fixes, extensions, documentation, pretty much anything that
helps improve Designate, contributing is easy & follows
the standard OpenStack `Gerrit workflow`_, if you're looking for
something to do, you could always checkout the blueprint_ & bug_
lists.

The designate git repo is available at https://opendev.org/openstack/designate,
though all contributions should be done via the Gerrit review system.

Task Tracking
-------------

We track our tasks in Launchpad

   https://bugs.launchpad.net/designate

If you're looking for some smaller, easier work item to pick up and get started
on, search for the 'low-hanging-fruit' tag.

Reporting a Bug
---------------

You found an issue and want to make sure we are aware of it? You can
do so on `Launchpad <https://bugs.launchpad.net/designate>`_.

Development Environment and Developer Workflow
----------------------------------------------

Assuming you've already got a working :ref:`Development Environment`,
here's a quick summary:

Install the git-review package to make life easier, some distros have
it as native package, otherwise use pip

.. code-block:: shell-session

  pip install git-review

Branch, work, & submit:

.. code-block:: shell-session

  # cut a new branch, tracking master
  git checkout --track -b bug/id origin/master
  # work work work
  git add stuff
  git commit
  # rebase/squash to a single commit before submitting
  git rebase -i
  # submit
  git-review

Coding Standards
----------------

Designate uses the OpenStack flake8 coding standards guidelines.
These are stricter than pep8, and are run by gerrit on every commit.

You can use tox to check your code locally by running

.. code-block:: shell-session

  # For just flake8 tests
  tox -e flake8
  # For tests + flake8
  tox

Example DNS Names and IP Space
''''''''''''''''''''''''''''''

The IANA has allocated several special purpose domains and IP blocks for use as
examples in code and documentation. Where possible, these domains and IP blocks
should be preferred. There are some cases where it will not be possible to
follow this guidance, for example, there is currently no reserved IDN domain
name.

We prefer to use these names and IP blocks to avoid causing any unexpected
collateral damage to the rightful owners of the non-reserved names and
IP space. For example, publishing an email address in our codebase will
more than likely be picked up by spammers, while published URLs etc using
non-reserved names or IP space will likely trigger search indexers etc
to begin crawling.

Reserved Domains
~~~~~~~~~~~~~~~~

Reserved DNS domains are documented here: `IANA Special Use Domain Names`_.

Several common reserved domains:

* example.com.
* example.net.
* example.org.

Reserved IP Space
~~~~~~~~~~~~~~~~~

Reserved IP space is documented here: `IANA IPv4 Special Registry`_, and
`IANA IPv6 Special Registry`_.

Several common reserved IP blocks:

* 192.0.2.0/24
* 198.51.100.0/24
* 203.0.113.0/24
* 2001:db8::/32

.. _IANA Special Use Domain Names: https://www.iana.org/assignments/special-use-domain-names/special-use-domain-names.xhtml
.. _IANA IPv4 Special Registry: https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml
.. _IANA IPv6 Special Registry: https://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml

Style Guide
'''''''''''

Follow `OpenStack Style Guidelines <https://docs.openstack.org/hacking/latest/>`_

File header
~~~~~~~~~~~

Start new files with the following. Replace where needed:

.. code-block:: python

    # Copyright <year> <company>
    #
    # Author: <name> <email addr>
    #
    # Licensed under the Apache License, Version 2.0 (the "License"); you may
    # not use this file except in compliance with the License. You may obtain
    # a copy of the License at
    #
    #      http://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    # WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    # License for the specific language governing permissions and limitations
    # under the License.

    """
    <package.module>
    ~~~~~~~~~~~~~~
    <Describe what the module should do, especially interactions with
    other components and caveats>

    <Optional links>
    `Specs: Refer to a spec document if relevant`_

    `User documentation <FILL_THIS.html>`_ <Refer to files under doc/>
    <This is useful to remind developers to keep the docs up to date>
    """

Example:

.. code-block:: rst

    backend.impl_akamai
    ~~~~~~~~~~~~~~~~~~~
    Akamai backend. Create and delete zones on Akamai. Blah Blah...

    `Specs: Keystone Session <https://opendev.org/openstack/designate-specs/src/branch/master/specs/kilo/switch-to-keystone-session.rst>`_

    `User documentation <backend.html>`_

When updating a module, please ensure that the related user documentation is
updated as well.

Docstrings
~~~~~~~~~~

Use the Sphinx markup. Here is an example:

.. code-block:: python

    class MyClass(object):
        """<description>
        mention a function :func:`foo` or a class :class:`Bar`
        """

        def function(self, foo):
            """<describe what the function does>
            :param foo: <description>
            :type foo: <type>
            :returns: <describe the returned value>
            :rtype: <returned type>
            :raises: <list raised exceptions>

            :Example:

            >>> a = b - c
            >>> <more Python code>

            .. note:: <add a note here>
            .. seealso:: <blah>
            .. warning:: <use sparingly>
            """

Logging
~~~~~~~

See https://docs.openstack.org/oslo.i18n/latest/user/guidelines.html

.. code-block:: python

    # Do not use "%" string formatting
    # No localization for log messages
    LOG.debug("... %s", variable)
    # Use named interpolation when more than one replacement is done
    LOG.info("... %(key)s ...", {'key': 'value', ...})
    LOG.warning("... %(key)s", {'key': 'value'})
    LOG.error("... %(key)s", {'key': 'value'})
    LOG.critical("... %(key)s", {'key': 'value'})

.. _Gerrit workflow: https://docs.openstack.org/infra/manual/developers.html#development-workflow
.. _blueprint: https://blueprints.launchpad.net/designate
.. _bug: https://bugs.launchpad.net/designate
