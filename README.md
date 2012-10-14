# Introduction

Moniker is an OpenStack inspired DNSaaS.

# Developer Guide:

NOTE: This is probably incomplete!

## Install Dependencies

1. `apt-get install python-pip python-virtualenv python-setuptools-git`
1. `apt-get install rabbitmq-server bind9`
1. `apt-get build-dep python-lxml`

## Install Moniker

1. `virtualenv .venv`
1. `source .venv/bin/activate`
1. `python setup.py develop`
1. create config files (See `*.sample` in the `etc` folder)
1. Ensure the user you intend to run moniker as has passwordless sudo rights:
   * `echo "$USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-moniker-$USER`
   * `chmod 0440 /etc/sudoers.d/90-moniker-$USER`
1. Tell bind to load our zones:
   * Open `/etc/bind/named.conf`
   * Add `include "$CHECKOUT_PATH/var/bind9/zones.config";` to the end of the file
   * `sudo service bind9 restart`

## Run

1. Open 3 consoles/screen sessions for each command:
  * `./bin/moniker-api`
  * `./bin/moniker-central`
  * `./bin/moniker-agent-bind9`
1. Make use of the API..

# TODOs:

* Documentation!
* Fixup Bind9 agent implementation so it could be considered even remotely reliable
* Re-Add PowerDNS agent implementation.
* Database migrations
* Unit Tests!!
* Integration with other OS servers eg Nova and Quantum
  * Listen for floating IP allocation/deallocation events - giving user access to
  the necessary PTR record.
  * Listen for server create/destroy events - creating DNS records as needed.
  * Listen for server add/remove from security group events - creating "load balancing" DNS RR records as needed.
* Introduce Server Pools
  * Server pools will allow a provider to 'schedule' a end users domain to one of many available DNS server pools
