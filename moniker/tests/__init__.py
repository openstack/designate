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
import sys
import unittest
import mox
from contextlib import contextmanager
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common.context import RequestContext, get_admin_context
from moniker import storage
from moniker.central import service as central_service

LOG = logging.getLogger(__name__)


class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()

        self.mox = mox.Mox()
        self.config(database_connection='sqlite://',
                    rpc_backend='moniker.openstack.common.rpc.impl_fake',
                    notification_driver=[])
        storage.setup_schema()

        self.admin_context = self.get_admin_context()

    def tearDown(self):
        storage.teardown_schema()
        cfg.CONF.reset()
        self.mox.UnsetStubs()

        super(TestCase, self).tearDown()

    def config(self, **kwargs):
        group = kwargs.pop('group', None)
        for k, v in kwargs.iteritems():
            cfg.CONF.set_override(k, v, group)

    def get_central_service(self):
        return central_service.Service()

    def get_context(self, **kwargs):
        return RequestContext(**kwargs)

    def get_admin_context(self):
        return get_admin_context()

    if sys.version_info < (2, 7):
        # Add in some of the nicer methods not present in 2.6
        def assertIsNone(self, expr, msg=None):
            return self.assertEqual(expr, None, msg)

        def assertIsNotNone(self, expr, msg=None):
            return self.assertNotEqual(expr, None, msg)

        def assertIn(self, test_value, expected_set):
            msg = "%s did not occur in %s" % (test_value, expected_set)
            self.assert_(test_value in expected_set, msg)

        def assertNotIn(self, test_value, expected_set):
            msg = "%s occurred in %s" % (test_value, expected_set)
            self.assert_(test_value not in expected_set, msg)

        def assertGreaterEqual(self, a, b, msg=None):
            if not msg:
                msg = '%r not greater than or equal to %r' % (a, b)

            self.assert_(a >= b, msg)

        def assertLessEqual(self, a, b, msg=None):
            if not msg:
                msg = '%r not less than or equal to %r' % (a, b)

        def assertRaises(self, excClass, callableObj=None, *args, **kwargs):
            @contextmanager
            def context():
                raised = None
                try:
                    yield
                except Exception, e:
                    raised = e
                finally:
                    if not isinstance(raised, excClass):
                        raise self.failureException(
                            "%s not raised" % str(excClass))

            if callableObj is None:
                return context()
            with context:
                callableObj(*args, **kwargs)
