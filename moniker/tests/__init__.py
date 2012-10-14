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
import unittest
import mox
from moniker.openstack.common import cfg
from moniker.openstack.common.context import RequestContext, get_admin_context
from moniker.database import reinitialize as reinitialize_database
from moniker.database import sqlalchemy  # Import for sql_connection cfg def.


class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.mox = mox.Mox()
        self.config(database_driver='sqlalchemy', sql_connection='sqlite://',
                    rpc_backend='moniker.openstack.common.rpc.impl_fake',
                    notification_driver=[])
        reinitialize_database()

    def tearDown(self):
        cfg.CONF.reset()
        self.mox.UnsetStubs()
        super(TestCase, self).tearDown()

    def config(self, **kwargs):
        group = kwargs.pop('group', None)
        for k, v in kwargs.iteritems():
            cfg.CONF.set_override(k, v, group)

    def get_context(self, **kwargs):
        return RequestContext(**kwargs)

    def get_admin_context(self):
        return get_admin_context()
