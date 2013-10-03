================
Getting Involved
================

#openstack-dns
--------------
There is an active IRC channel at irc://freenode.net/#openstack-dns, where many of the designate contributors can be found, as
well as users from various organisations.

Contributing
------------
We welcome fixes, extensions, documentation, pretty much anything that helps improve Designate, contributing is easy & follows
the standard OpenStack `Gerrit workflow`_, if you're looking for something to do, you could always checkout the blueprint_ & bug_
lists.

Assuming you've already got a working :ref:`Development Environment`, here's a quick summary:

Install the git-review package to make life easier

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
  
.. _Gerrit workflow: https://wiki.openstack.org/wiki/Gerrit_Workflow
.. _blueprint: https://blueprints.launchpad.net/designate
.. _bug: https://bugs.launchpad.net/designate
