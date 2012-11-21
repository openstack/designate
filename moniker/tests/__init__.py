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
import unittest2
import mox
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.context import MonikerContext
from moniker import storage
from moniker.api import service as api_service
from moniker.central import service as central_service

LOG = logging.getLogger(__name__)


class TestCase(unittest2.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()

        self.mox = mox.Mox()
        self.config(
            database_connection='sqlite://',
            rpc_backend='moniker.openstack.common.rpc.impl_fake',
            notification_driver=[],
            backend_driver='fake',
            auth_strategy='noauth'
        )
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

    def get_api_service(self):
        return api_service.Service()

    def get_central_service(self):
        return central_service.Service()

    def get_context(self, **kwargs):
        return MonikerContext(**kwargs)

    def get_admin_context(self):
        return MonikerContext.get_admin_context()

    # Fixture methods
    def create_server(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())

        values = dict(
            name='ns1.example.org',
            ipv4='192.0.2.1',
            ipv6='2001:db8::1',
        )

        values.update(kwargs)

        return self.central_service.create_server(context, values=values)

    def create_domain(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())

        values = dict(
            name='example.com',
            email='info@example.com',
        )

        values.update(kwargs)

        return self.central_service.create_domain(context, values=values)

    def create_record(self, domain_id, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())

        values = dict(
            name='www.example.com',
            type='A',
            data='127.0.0.1'
        )

        values.update(kwargs)

        return self.central_service.create_record(context, domain_id,
                                                  values=values)
