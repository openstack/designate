.. _designate-manage:

====================
Designate Manage CLI
====================

This chapter documents :command:`designate-manage`

For help on a specific :command:`designate` command, enter:

.. code-block:: console

   $ designate-manage COMMAND --help

.. _designate_manage_command_usage:

designate-manage
================

designate-manage usage
----------------------

.. code-block:: console

   usage: designate-manage [-h] [--config-dir DIR] [--config-file PATH] [--debug]
                           [--log-config-append PATH] [--log-date-format DATE_FORMAT]
                           [--log-dir LOG_DIR] [--log-file PATH] [--nodebug]
                           [--nouse-syslog] [--nouse-syslog-rfc-format] [--noverbose]
                           [--nowatch-log-file]
                           [--syslog-log-facility SYSLOG_LOG_FACILITY] [--use-syslog]
                           [--use-syslog-rfc-format] [--verbose] [--version]
                           [--watch-log-file]

.. _designate_command_options:

designate optional arguments
----------------------------

``--config-dir DIR``
  Path to a config directory to pull \*.conf files from.
  This file set is sorted, so as to provide a
  predictable parse order if individual options are
  over-ridden. The set is parsed after the file(s)
  specified via previous --config-file, arguments hence
  over-ridden options in the directory take precedence.

``--config-file PATH``
  Path to a config file to use. Multiple config files
  can be specified, with values in later files taking
  precedence. Defaults to None.

``--debug, -d``
  If set to true, the logging level will be set to DEBUG
  instead of the default INFO level.

``--log-config-append PATH, --log_config PATH``
  The name of a logging configuration file. This file is
  appended to any existing logging configuration files.
  For details about logging configuration files, see the
  Python logging module documentation. Note that when
  logging configuration files are used then all logging
  configuration is set in the configuration file and
  other logging configuration options are ignored (for
  example, logging_context_format_string).

``--log-date-format DATE_FORMAT``
  Defines the format string for %(asctime)s in log
  records. Default: None . This option is ignored if
  log_config_append is set.

``--log-dir LOG_DIR, --logdir LOG_DIR``
  (Optional) The base directory used for relative
  log_file paths. This option is ignored if
  log_config_append is set.

``--log-file PATH, --logfile PATH``
  (Optional) Name of log file to send logging output to.
  If no default is set, logging will go to stderr as
  defined by use_stderr. This option is ignored if
  log_config_append is set.

``--nodebug``
  The inverse of --debug

``--nouse-syslog``
  The inverse of --use-syslog

``--nouse-syslog-rfc-format``
  The inverse of --use-syslog-rfc-format

``--noverbose``
  The inverse of --verbose

``--nowatch-log-file``
  The inverse of --watch-log-file

``--syslog-log-facility SYSLOG_LOG_FACILITY``
  Syslog facility to receive log lines. This option is
  ignored if log_config_append is set.

``--use-syslog``
  Use syslog for logging. Existing syslog format is
  DEPRECATED and will be changed later to honor RFC5424.
  This option is ignored if log_config_append is set.

``--use-syslog-rfc-format``
  Enables or disables syslog rfc5424 format for logging.
  If enabled, prefixes the MSG part of the syslog
  message with APP-NAME (RFC5424). This option is
  ignored if log_config_append is set.

``--verbose, -v``
  If set to false, the logging level will be set to
  WARNING instead of the default INFO level.

``--watch-log-file``
  Uses logging handler designed to watch file system.
  When log file is moved or removed this handler will
  open a new log file with specified path
  instantaneously. It makes sense only if log_file
  option is specified and Linux platform is used. This
  option is ignored if log_config_append is set.


.. _designate_manage_pool:

designate-manage pool
=====================

.. code-block:: console

    usage: designate pool [-h] {generate_file,show_config,update} ...

    positional arguments:
      {generate_file,show_config,update}

.. _designate_manage_pool_generate_file:

designate-manage pool generate_file
-----------------------------------

.. code-block:: console

    usage: designate-manage pool generate_file [-h] [--file FILE]


Export a YAML copy of the current running pool config

**Optional arguments:**

``-h, --help``
  show this help message and exit

``--file FILE``
  The path to the file the yaml output should be written to
  (Defaults to /etc/designate/pools.yaml)

.. _designate_manage_pool_update:

designate-manage pool update
----------------------------

.. code-block:: console

    usage: designate-manage pool update [-h] [--file FILE] [--delete]
                                        [--dry-run]


Update the running pool config from a YAML file

**Optional arguments:**

``-h, --help``
  show this help message and exit

``--file FILE``
  The path to the file that should be used to update the pools config
  (Defaults to /etc/designate/pools.yaml)

``--delete``
  Any Pools not listed in the config file will be deleted.
  .. warning::  This will delete any zones left in this pool

``--dry-run``
  This will simulate what will happen when you run this command

.. _designate_manage_pool_show:

designate-manage pool show
--------------------------

.. code-block:: console

    usage: designate-manage pool show_config [-h] [--pool_id POOL_ID]
                                             [--all_pools]


Show the deployed pools configuration

**Optional arguments:**

``-h, --help``
  show this help message and exit

``--pool_id POOL_ID``
  ID of the pool to be examined

``--all_pools``
  show the config of all the pools

.. _designate_manage_database:

designate-manage database
=========================

.. _designate_manage_database_sync:

designate-manage database sync
------------------------------

.. code-block:: console

    usage: designate-manage database sync [-h] [--revision REVISION]


Update the designate database schema

**Optional arguments:**

``-h, --help``
  show this help message and exit

``--revision REVISION``
  The version that the designate database should be synced to.
  (Defaults to latest version)


.. _designate_manage_database_version:

designate-manage database version
---------------------------------

.. code-block:: console

    usage: designate-manage database version [-h]


Show what version of the database schema is currently in place

**Optional arguments:**

``-h, --help``
  show this help message and exit

.. _designate_manage_powerdns:
