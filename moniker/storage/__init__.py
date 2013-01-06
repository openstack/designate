# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.storage.base import StorageEngine

LOG = logging.getLogger(__name__)


def get_engine(engine_name):
    """
    Return the engine class from the provided engine name
    """
    return StorageEngine.get_plugin(engine_name, invoke_on_load=True)


def get_connection():
    engine = get_engine(cfg.CONF.storage_driver)
    return engine.get_connection()


def setup_schema():
    """ Create the DB - Used for testing purposes """
    LOG.debug("Setting up Schema")
    connection = get_connection()
    connection.setup_schema()


def teardown_schema():
    """ Reset the DB to default - Used for testing purposes """
    LOG.debug("Tearing down Schema")
    connection = get_connection()
    connection.teardown_schema()
