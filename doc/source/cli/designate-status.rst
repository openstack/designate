====================
Designate Status CLI
====================

This chapter documents :command:`designate-status`.

For help on a specific :command:`designate-status` command, enter:

.. code-block:: console

   $ designate-status COMMAND --help

designate-status
================

:program:`designate-status` is a tool that provides routines for checking the
status of a Designate deployment.

The standard pattern for executing a :program:`designate-status` command is:

.. code-block:: console

    designate-status <category> <command> [<args>]

Run without arguments to see a list of available command categories:

.. code-block:: console

    designate-status

Categories are:

* ``upgrade``

Detailed descriptions are below.

You can also run with a category argument such as ``upgrade`` to see a list of
all commands in that category:

.. code-block:: console

    designate-status upgrade

The following sections describe the available categories and arguments for
:program:`designate-status`.

designate-status upgrade
========================

.. _designate-status-upgrade-check:

designate-status upgrade check
------------------------------

``designate-status upgrade check``
  Performs a release-specific readiness check before running db sync for the
  new version. This command expects to have complete configuration and access
  to the database.

  **Return Codes**

  .. list-table::
     :widths: 20 80
     :header-rows: 1

     * - Return code
       - Description
     * - 0
       - All upgrade readiness checks passed successfully and there is nothing
         to do.
     * - 1
       - At least one check encountered an issue and requires further
         investigation. This is considered a warning but the upgrade may be OK.
     * - 2
       - There was an upgrade status check failure that needs to be
         investigated. This should be considered something that stops an
         upgrade.
     * - 255
       - An unexpected error occurred.

  **History of Checks**

  **8.0.0 (Stein)**

  * Checks that duplicate entries do not exist in the ``service_statuses``
    table.
