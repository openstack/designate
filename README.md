# Introduction

Designate is an OpenStack inspired DNSaaS.

Docs: http://designate.readthedocs.org and some below for now.
Bugs / Blueprints: http://launchpad.net/moniker

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


# Development
Designate follows the [OpenStack Gerrit Workflow](https://wiki.openstack.org/wiki/Gerrit_Workflow)

## Setup
Setup a working environment:

````
git clone git@github.com:stackforge/designate.git
cd designate
virtualenv .venv
. .venv/bin/activate
pip install -r requirements.txt -r test-requirements.txt
python setup.py develop
````

## Contributing
Install the git-review package to make life easier

````
pip install git-review
````

Branch, work, & submit:

````
# cut a new branch, tracking master
git checkout --track -b bug/id origin/master
# work work work
git add stuff
git commit
# rebase/squash to a single commit before submitting
git rebase -i
# submit
git-review
````


