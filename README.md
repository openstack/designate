# Introduction

Designate is an OpenStack inspired DNSaaS.

Docs: http://designate.rtfd.org and some below for now.
Bugs / Blueprints: http://launchpad.net/designate

IRC: #openstack-dns

Installation: http://designate.readthedocs.org/en/latest/install.html

# TODOs:

* Documentation!
* Fixup Bind9 agent implementation so it could be considered even remotely reliable
* Re-Add PowerDNS agent implementation.
* Unit Tests!!
* Integration with other OS servers eg Nova and Quantum
  * Listen for floating IP allocation/deallocation events - giving user access to
  the necessary PTR record.
  * Listen for server create/destroy events - creating DNS records as needed.
  * Listen for server add/remove from security group events - creating "load balancing" DNS RR records as needed.
* Introduce Server Pools
  * Server pools will allow a provider to 'schedule' a end users domain to one of many available DNS server pools
