# Copyright 2012 Managed I.T.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
from __future__ import absolute_import

import os
import random
import shutil
import tempfile
from contextlib import contextmanager

import fixtures
from oslo_log import log as logging
from oslo_utils import importutils
from oslo_config import cfg
import tooz.coordination

from designate import policy
from designate import network_api
from designate import rpc
from designate.network_api import fake as fake_network_api
from designate.sqlalchemy import utils as sqlalchemy_utils

"""Test fixtures
"""

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

    def setUp(self):
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

    fixtures = {}

    @staticmethod
    def get_fixture(repo_path, init_version=None):
        if repo_path not in DatabaseFixture.fixtures:
            DatabaseFixture.fixtures[repo_path] = DatabaseFixture(
                repo_path, init_version)
        return DatabaseFixture.fixtures[repo_path]

    def _mktemp(self):
        """Create temporary database file
        """
        tmpfs_path = "/dev/shm"
        if os.path.isdir(tmpfs_path):
            tmp_dir = tmpfs_path
            LOG.debug("Using tmpfs on %s as database tmp dir" % tmp_dir)
        else:
            tmp_dir = "/tmp"
            LOG.warning("Using %s as database tmp dir. Tests might be slow" %
                        tmp_dir)

        _, path = tempfile.mkstemp(prefix='designate-', suffix='.sqlite',
                                   dir=tmp_dir)
        return path

    def __init__(self, repo_path, init_version=None):
        super(DatabaseFixture, self).__init__()

        # Create the Golden DB
        self.golden_db = self._mktemp()
        self.golden_url = 'sqlite:///%s' % self.golden_db

        # Migrate the Golden DB
        manager = sqlalchemy_utils.get_migration_manager(
            repo_path, self.golden_url, init_version)
        manager.upgrade(None)

        # Prepare the Working Copy DB
        self.working_copy = self._mktemp()
        self.url = 'sqlite:///%s' % self.working_copy

    def setUp(self):
        super(DatabaseFixture, self).setUp()
        shutil.copyfile(self.golden_db, self.working_copy)

    def tearDown(self):
        # This is currently unused
        super(DatabaseFixture, self).tearDown()
        LOG.debug("Deleting %s" % self.working_copy)
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


@contextmanager
def random_seed(seed):
    """Context manager to set random.seed() temporarily
    """
    state = random.getstate()
    random.seed(seed)
    yield
    random.setstate(state)
