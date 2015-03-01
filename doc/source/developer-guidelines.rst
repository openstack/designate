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

Reserverd DNS domains are documented here: `IANA Special Use Domain Names`_.

Several common reserved domains:

* example.com.
* example.net.
* example.org.

Reserved IP Space
-----------------

Reserverd IP space is documented here: `IANA IPv4 Special Registry`_, and
`IANA IPv6 Special Registry`_.

Several common reserved IP blocks:

* 192.0.2.0/24
* 198.51.100.0/24
* 203.0.113.0/24
* 2001:db8::/32
  
.. _IANA Special Use Domain Names: http://www.iana.org/assignments/special-use-domain-names/special-use-domain-names.xhtml
.. _IANA IPv4 Special Registry: http://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml
.. _IANA IPv6 Special Registry: http://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml
