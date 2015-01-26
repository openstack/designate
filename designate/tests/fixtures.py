# Copyright 2012 Managed I.T.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import shutil
import tempfile

import fixtures
from oslo_log import log as logging
from oslo_utils import importutils
from oslo.config import cfg
from oslo.messaging.notify import _impl_test as test_notifier

from designate import policy
from designate import network_api
from designate import rpc
from designate.network_api import fake as fake_network_api
from designate.sqlalchemy import utils as sqlalchemy_utils


LOG = logging.getLogger(__name__)


class NotifierFixture(fixtures.Fixture):
    def setUp(self):
        super(NotifierFixture, self).setUp()
        self.addCleanup(test_notifier.reset)

    def get(self):
        return test_notifier.NOTIFICATIONS

    def clear(self):
        return test_notifier.reset()


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
    def __init__(self, svc_name, *args, **kw):
        cls = importutils.import_class(
            'designate.%s.service.Service' % svc_name)
        self.svc = cls.create(binary='designate-' + svc_name, *args, **kw)

    def setUp(self):
        super(ServiceFixture, self).setUp()
        self.svc.start()
        self.addCleanup(self.kill)

    def kill(self):
        try:
            self.svc.kill()
        except Exception:
            pass


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
        _, path = tempfile.mkstemp(prefix='designate-', suffix='.sqlite',
                                   dir='/tmp')
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


class NetworkAPIFixture(fixtures.Fixture):
    def setUp(self):
        super(NetworkAPIFixture, self).setUp()
        self.api = network_api.get_network_api(cfg.CONF.network_api)
        self.fake = fake_network_api
        self.addCleanup(self.fake.reset_floatingips)
