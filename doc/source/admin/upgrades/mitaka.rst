..
    Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

********************************
Upgrading to Mitaka from Liberty
********************************

Pools Configuration
===================

We have updated how the config data for pools is now stored.

Previously there was a mix of content in the ``designate.conf`` file and in the
designate database.

We have moved all of the data to the database in Mitaka, to avoid confusion,
and avoid the massive complexity that exists in the config file.

.. warning:: This part of the upgrade **requires** downtime.

We have 2 new commands in the ``designate-manage`` utility that are
able to assist the migration.

To make the config syntax simpler we have a new YAML based config file that is
used to load information into the database.

.. literalinclude:: ../../../../etc/designate/pools.yaml.sample
       :language: yaml

We have a command that will allow you to take your current running config, and
export it to the new YAML format.

.. note::

    You will need to have at least one instance of central running, and machine
    ``designate-manage`` is running on will need access to the messaging queue

.. code-block:: console

    designate-manage pool generate_file --file output.yml

This will create a YAML file, with all the currently defined pools, and all
of their config.

We suggest this is then migrated into a config management system,
or other document management system.

From this point on all updates to pools should be done by updating this file,
and running:

.. code-block:: console

    designate-manage pool update --file /path/to/file.yml


Pools - Step by Step
--------------------

1. Ensure there is not 2 pools with the same name.
2. Stop all Designate Services.
3. Deploy new Mitaka code
4. Start ``designate-central``
5. Run
    .. code-block:: console

        designate-manage pool export_from_config --file output.yml

6. Ensure the output file is correct (reference sample file for each value)
7. Run

    .. code-block:: console

        designate-manage pool update --file output.yml --dry_run True --delete True

8. Ensure the output of this command is not removing any Pools
9. Run

   .. code-block:: console

        designate-manage pool update --file output.yml --delete True

10. Start the remaining designate services.
