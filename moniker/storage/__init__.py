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
from urlparse import urlparse
from stevedore import driver
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging

LOG = logging.getLogger(__name__)

DRIVER_NAMESPACE = 'moniker.storage'

cfg.CONF.register_opts([
    cfg.StrOpt('database-connection',
               default='sqlite:///$state_path/moniker.sqlite',
               help='The database driver to use')
])


def get_engine_name(string):
    """
    Return the engine name from either a non-dialected or dialected string
    """
    return string.split("+")[0]


def get_engine(conf):
    scheme = urlparse(conf.database_connection).scheme
    engine_name = get_engine_name(scheme)
    LOG.debug('Looking for %r engine in %r', engine_name, DRIVER_NAMESPACE)
    mgr = driver.DriverManager(DRIVER_NAMESPACE, engine_name)
    mgr.driver.register_opts(conf)
    return mgr.driver()


def get_connection(conf):
    engine = get_engine(conf)
    return engine.get_connection(conf)


def setup_schema():
    """ Create the DB - Used for testing purposes """
    LOG.debug("Setting up Schema")
    connection = get_connection(cfg.CONF)
    connection.setup_schema()


def teardown_schema():
    """ Reset the DB to default - Used for testing purposes """
    LOG.debug("Tearing down Schema")
    connection = get_connection(cfg.CONF)
    connection.teardown_schema()
