********************
Developer Guidelines
********************


Example DNS Names and IP Space
==============================

The IANA has allocated several special purpose domains and IP blocks for use as
examples in code and documentation. Where possible, these domains and IP blocks
should be preferred. There are some cases where it will not be possible to
follow this guidance, for example, there is currently no reserved IDN domain
name.

We prefer to use these names and IP blocks to avoid causing any unexpected
collateral damage to the rightful owners of the non-reserved names and IP space.
For example, publishing an email address in our codebase will more than likely
be picked up by spammers, while published URLs etc using non-reserved names or
IP space will likely trigger search indexers etc to begin crawling. 

Reserved Domains
----------------

Reserved DNS domains are documented here: `IANA Special Use Domain Names`_.

Several common reserved domains:

* example.com.
* example.net.
* example.org.

Reserved IP Space
-----------------

Reserved IP space is documented here: `IANA IPv4 Special Registry`_, and
`IANA IPv6 Special Registry`_.

Several common reserved IP blocks:

* 192.0.2.0/24
* 198.51.100.0/24
* 203.0.113.0/24
* 2001:db8::/32

.. _IANA Special Use Domain Names: http://www.iana.org/assignments/special-use-domain-names/special-use-domain-names.xhtml
.. _IANA IPv4 Special Registry: http://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml
.. _IANA IPv6 Special Registry: http://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml

Style Guide
===========

Follow `OpenStack Style Guidelines <http://docs.openstack.org/developer/hacking/>`_

File header
-----------

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
    `Specs: Refer to to a spec document if relevant`_

    `User documentation <FILL_THIS.html>`_ <Refer to files under doc/>
    <This is useful to remind developers to keep the docs up to date>
    """

Example:

.. code-block:: rst

    backend.impl_akamai
    ~~~~~~~~~~~~~~~~~~~
    Akamai backend. Create and delete zones on Akamai. Blah Blah...

    `Specs: Keystone Session <https://github.com/openstack/designate-specs/blob/master/specs/kilo/switch-to-keystone-session.rst>`_

    `User documentation <backend.html>`_

When updating a module, please ensure that the related user documentation is updated as well.

Docstrings
----------

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
-------

See http://docs.openstack.org/developer/oslo.i18n/guidelines.html

.. code-block:: python

    # Do not use "%" string formatting
    # No localization for debug
    LOG.debug("... %s", variable)
    LOG.info(_LI("... %s..."), variable)
    # Use named interpolation when more than one replacement is done
    LOG.info(_LI("... %(key)s ..."), {'key': 'value', ...})
    LOG.warn(_LW("... %(key)s"), {'key': 'value'})
    LOG.error(_LE("... %(key)s"), {'key': 'value'})
    LOG.critical(_LC("... %(key)s"), {'key': 'value'})
