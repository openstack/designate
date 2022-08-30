# Copyright 2012 Managed I.T.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from unittest import mock

from contextlib import contextmanager
import logging as std_logging
import os
import random
import shutil
import tempfile

import fixtures
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils
import tooz.coordination

from designate.manage import database as db_commands
from designate import network_api
from designate.network_api import fake as fake_network_api
from designate import policy
from designate import rpc
import designate.service
import designate.utils

"""Test fixtures
"""
_TRUE_VALUES = ('True', 'true', '1', 'yes')
LOG = logging.getLogger(__name__)


class CoordinatorFixture(fixtures.Fixture):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def setUp(self):
        super(CoordinatorFixture, self).setUp()
        self.coordinator = tooz.coordination.get_coordinator(
            *self._args, **self._kwargs)

        self.coordinator.start()
        self.addCleanup(self.coordinator.stop)


class RPCFixture(fixtures.Fixture):

    def __init__(self, conf):
        self.conf = conf

    def setUp(self):
        super(RPCFixture, self).setUp()
        rpc.init(self.conf)
        self.addCleanup(self.deinit)

    def deinit(self):
        if rpc.initialized():
            rpc.cleanup()


class ServiceFixture(fixtures.Fixture):
    def __init__(self, svc_name):
        cls = importutils.import_class(
            'designate.%s.service.Service' % svc_name)
        self.svc = cls()
        self.svc_name = svc_name

    @mock.patch.object(designate.service.DNSService, '_start')
    def setUp(self, mock_start):
        super(ServiceFixture, self).setUp()
        LOG.info('Starting service %s (%s)', self.svc_name, id(self.svc))
        self.svc.start()
        self.addCleanup(self.stop)

    def stop(self):
        LOG.info('Stopping service %s (%s)', self.svc_name, id(self.svc))

        try:
            self.svc.stop()

        except Exception:
            LOG.error('Failed to stop service %s (%s)',
                      self.svc_name, id(self.svc))
            raise

        finally:
            # Always try reset the service's RPCAPI
            mod = importutils.try_import('designate.%s.rpcapi' % self.svc_name)
            if hasattr(mod, 'reset'):
                LOG.info('Resetting service %s RPCAPI', self.svc_name)
                mod.reset()


class PolicyFixture(fixtures.Fixture):
    def setUp(self):
        super(PolicyFixture, self).setUp()
        self.addCleanup(policy.reset)


class DatabaseFixture(fixtures.Fixture):

    fixture = None

    @staticmethod
    def get_fixture():
        if not DatabaseFixture.fixture:
            DatabaseFixture.fixture = DatabaseFixture()
        return DatabaseFixture.fixture

    def _mktemp(self):
        """Create temporary database file
        """
        tmpfs_path = "/dev/shm"
        if os.path.isdir(tmpfs_path):
            tmp_dir = tmpfs_path
            LOG.debug("Using tmpfs on %s as database tmp dir", tmp_dir)
        else:
            tmp_dir = "/tmp"
            LOG.warning("Using %s as database tmp dir. Tests might be slow",
                        tmp_dir)

        _, path = tempfile.mkstemp(prefix='designate-', suffix='.sqlite',
                                   dir=tmp_dir)
        return path

    def __init__(self):
        super(DatabaseFixture, self).__init__()

        # Create the Golden DB
        self.golden_db = self._mktemp()
        self.golden_url = 'sqlite:///%s' % self.golden_db

        # Migrate the Golden DB
        db_cmds = db_commands.DatabaseCommands()
        db_cmds.upgrade('head', db_url=self.golden_url)

        # Prepare the Working Copy DB
        self.working_copy = self._mktemp()
        self.url = 'sqlite:///%s' % self.working_copy

    def setUp(self):
        super(DatabaseFixture, self).setUp()
        shutil.copyfile(self.golden_db, self.working_copy)

    def tearDown(self):
        # This is currently unused
        super(DatabaseFixture, self).tearDown()
        LOG.debug("Deleting %s", self.working_copy)
        os.unlink(self.working_copy)


class NetworkAPIFixture(fixtures.Fixture):
    def setUp(self):
        super(NetworkAPIFixture, self).setUp()
        self.api = network_api.get_network_api(cfg.CONF.network_api)
        self.fake = fake_network_api
        self.addCleanup(self.fake.reset_floatingips)


class ZoneManagerTaskFixture(fixtures.Fixture):
    def __init__(self, task_cls):
        super(ZoneManagerTaskFixture, self).__init__()
        self._task_cls = task_cls

    def setUp(self):
        super(ZoneManagerTaskFixture, self).setUp()
        self.task = self._task_cls()
        self.task.on_partition_change(range(0, 4095), None, None)


# Logging handlers imported from Nova.

class NullHandler(std_logging.Handler):
    """custom default NullHandler to attempt to format the record.
    Used in conjunction with
    log_fixture.get_logging_handle_error_fixture to detect formatting errors in
    debug level logs without saving the logs.
    """
    def handle(self, record):
        self.format(record)

    def emit(self, record):
        pass

    def createLock(self):
        self.lock = None


class StandardLogging(fixtures.Fixture):
    """Setup Logging redirection for tests.
    There are a number of things we want to handle with logging in tests:
    * Redirect the logging to somewhere that we can test or dump it later.
    * Ensure that as many DEBUG messages as possible are actually
       executed, to ensure they are actually syntactically valid (they
       often have not been).
    * Ensure that we create useful output for tests that doesn't
      overwhelm the testing system (which means we can't capture the
      100 MB of debug logging on every run).
    To do this we create a logger fixture at the root level, which
    defaults to INFO and create a Null Logger at DEBUG which lets
    us execute log messages at DEBUG but not keep the output.
    To support local debugging OS_DEBUG=True can be set in the
    environment, which will print out the full debug logging.
    There are also a set of overrides for particularly verbose
    modules to be even less than INFO.
    """

    def setUp(self):
        super(StandardLogging, self).setUp()

        # set root logger to debug
        root = std_logging.getLogger()
        root.setLevel(std_logging.DEBUG)

        # supports collecting debug level for local runs
        if os.environ.get('OS_DEBUG') in _TRUE_VALUES:
            level = std_logging.DEBUG
        else:
            level = std_logging.INFO

        # Collect logs
        fs = '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        self.logger = self.useFixture(
            fixtures.FakeLogger(format=fs, level=None))
        # TODO(sdague): why can't we send level through the fake
        # logger? Tests prove that it breaks, but it's worth getting
        # to the bottom of.
        root.handlers[0].setLevel(level)

        if level > std_logging.DEBUG:
            # Just attempt to format debug level logs, but don't save them
            handler = NullHandler()
            self.useFixture(fixtures.LogHandler(handler, nuke_handlers=False))
            handler.setLevel(std_logging.DEBUG)

            # Don't log every single DB migration step
            std_logging.getLogger(
                'migrate.versioning.api').setLevel(std_logging.WARNING)

        # At times we end up calling back into main() functions in
        # testing. This has the possibility of calling logging.setup
        # again, which completely unwinds the logging capture we've
        # created here. Once we've setup the logging the way we want,
        # disable the ability for the test to change this.
        def fake_logging_setup(*args):
            pass

        self.useFixture(
            fixtures.MonkeyPatch('oslo_log.log.setup', fake_logging_setup))


@contextmanager
def random_seed(seed):
    """Context manager to set random.seed() temporarily
    """
    state = random.getstate()
    random.seed(seed)
    yield
    random.setstate(state)
