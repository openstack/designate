*********************
Production Guidelines
*********************

This document aims to provide a location for documented production
configurations and considerations. Including common misconfigurations, attack
mitigation techniques, and other relevant tips.

DNS Zone Squatting
==================

Designate's multi-tenant nature allows for any user to create (almost) any
zone, which can result in the legitimate owner being unable to create the zone
within Designate. There are several ways this can occur:

1. The squatter simply creates "example.com." in Designate before the
   legitimate owner can.

2. The squatter creates "foo.example.com." as a zone in Designate, preventing
   the creation of any parent zones (example.com., com.) by any other tenant.

3. The squatter creates "com." as a zone in Designate, preventing the creation
   of any zones ending in "com." by any other tenant.

4. The squatter creates "co.uk." as a zone in Designate, preventing the
   creation of any zones ending in "co.uk." by any other tenant.


Scenario #1 and #2 Mitigation
-----------------------------

There is no automated mitigation that can reasonably be performed here, DNS
providers have typically used a manual process, triggered through a support
request, to identify the legitimate owner and request the illegitimate owner
relinquish control, or action any other provider specific policy for handling
these scenarios.

Scenario #3 Mitigation
----------------------

This scenario can be mitigated by ensuring Designate has been configured, and
is updated periodically, with the latest list of gTLD's published as the
`IANA TLD list`_. These TLDs can be entered into Designate through the
`TLD API`_

Scenario #4 Mitigation
----------------------

This is a variation on Scenario #3, where public registration is available for
a second level domain, such as is the case with "co.uk.". Due to the nature of
public second level domains, where the IANA has no authority, these are not
included in the `IANA TLD list`_. A Mozilla sponsored initiative has stepped
up to fill this gap, crowdsourcing the list of "public suffixes", which
includes both standard TLDs and public second level domains. We recommend
configuring, and periodically updating, Designate with Mozilla's
`Public Suffix list`_. These public suffixes can be entered into Designate
through the `TLD API`_

DNS Cache Poisoning
===================

Multi-tenant nameservers can lead to an interesting variation of DNS Cache
Poisoning if nameservers are configured without consideration. Two tenants,
both owning different zones, can under the right circumstances inject content
into DNS responses for the other tenants zone. Let's consider an example:

Tenant A owns "example.com.", and has created an additional NS record within
their zone pointing to "ns.example.org." Tenant B, the attacker in this
example, can now create the "example.org." zone within their tenant. Within
this zone, they can legitimately create an A record with the name
"ns.example.org.". Under default configurations, many DNS servers (e.g. BIND),
will now include Tenant B's A record within responses for several queries
for "example.com.". Should the recursive resolver used by the end-user not be
configured to ignore out-of-bailiwick responses, this potentially invalid
A record for "ns.example.org." will be injected into the resolvers cache,
resulting in a cache poisoning attack.

This is an "interesting variation" of DNS cache poisoning, because the poison
records are returned by the authoritative nameserver for a given zone, rather
than in responses for the attackers zone.

`Bug 1471159`_ includes additional worked examples of this attack.

BIND9 Mitigation
----------------

BIND9 by default will include out-of-zone additionals, resulting is
susceptibility to this attack. We recommend BIND is configured to send minimal
responses - preventing the out-of-zone additionals from being processed.

In BIND's global options clause, include the following statement::

    minimal-responses yes;

PowerDNS Mitigation
-------------------

PowerDNS by default will include out-of-zone additionals, resulting is
susceptibility to this attack. We recommend setting the
`out-of-zone-additional-processing` configuration flag set to "no"  -
preventing the out-of-zone additionals from being processed.

In the main PowerDNS configuration file, include the following statement::

    out-of-zone-additional-processing=no

.. _IANA TLD list: https://data.iana.org/TLD/tlds-alpha-by-domain.txt
.. _Public Suffix list: https://publicsuffix.org/
.. _Bug 1471159: https://bugs.launchpad.net/designate/+bug/1471159
.. _TLD API: https://docs.openstack.org/api-ref/dns/#tld
