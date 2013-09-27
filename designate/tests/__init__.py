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
import copy
import unittest2
import mox
import nose
import os
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.openstack.common.notifier import test_notifier
from designate.openstack.common import policy
from designate.context import DesignateContext
from designate import storage
from designate import exceptions
from designate.agent import service as agent_service
from designate.api import service as api_service
from designate.central import service as central_service
from designate.sink import service as sink_service

LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('storage_driver', 'designate.central',
                    group='service:central')
cfg.CONF.import_opt('backend_driver', 'designate.agent',
                    group='service:agent')
cfg.CONF.import_opt('auth_strategy', 'designate.api',
                    group='service:api')
cfg.CONF.import_opt('database_connection', 'designate.storage.impl_sqlalchemy',
                    group='storage:sqlalchemy')


class TestCase(unittest2.TestCase):
    quota_fixtures = [{
        'tenant_id': '12345',
        'resource': 'domains',
        'hard_limit': 5,
    }, {
        'tenant_id': '12345',
        'resource': 'records',
        'hard_limit': 50,
    }]

    server_fixtures = [{
        'name': 'ns1.example.org.',
    }, {
        'name': 'ns2.example.org.',
    }, {
        'name': 'ns2.example.org.',
    }]

    tsigkey_fixtures = [{
        'name': 'test-key-one',
        'algorithm': 'hmac-md5',
        'secret': 'SomeSecretKey',
    }, {
        'name': 'test-key-two',
        'algorithm': 'hmac-sha256',
        'secret': 'AnotherSecretKey',
    }]

    domain_fixtures = [{
        'name': 'example.com.',
        'email': 'example@example.com',
    }, {
        'name': 'example.net.',
        'email': 'example@example.net',
    }, {
        'name': 'example.org.',
        'email': 'example@example.org',
    }]

    record_fixtures = [
        {'name': 'www.%s', 'type': 'A', 'data': '192.0.2.1'},
        {'name': 'mail.%s', 'type': 'A', 'data': '192.0.2.2'}
    ]

    def setUp(self):
        super(TestCase, self).setUp()

        self.mox = mox.Mox()

        self.config(
            notification_driver=[
                'designate.openstack.common.notifier.test_notifier',
            ],
            rpc_backend='designate.openstack.common.rpc.impl_fake',
        )

        self.config(
            storage_driver='sqlalchemy',
            backend_driver='fake',
            group='service:central'
        )

        self.config(
            backend_driver='fake',
            group='service:agent'
        )

        self.config(
            auth_strategy='noauth',
            group='service:api'
        )

        self.config(
            database_connection='sqlite://',
            group='storage:sqlalchemy'
        )

        storage.setup_schema()

        self.admin_context = self.get_admin_context()

    def tearDown(self):
        self.reset_notifications()
        policy.reset()
        storage.teardown_schema()
        cfg.CONF.reset()
        self.mox.UnsetStubs()
        super(TestCase, self).tearDown()

    def skip(self, message=None):
        raise nose.SkipTest(message)

    # Config Methods
    def config(self, **kwargs):
        group = kwargs.pop('group', None)

        for k, v in kwargs.iteritems():
            cfg.CONF.set_override(k, v, group)

    def policy(self, rules, default_rule='allow'):
        # Inject an allow and deny rule
        rules['allow'] = '@'
        rules['deny'] = '!'

        # Parse the rules
        rules = dict((k, policy.parse_rule(v)) for k, v in rules.items())
        rules = policy.Rules(rules, default_rule)

        # Set the rules
        policy.set_rules(rules)

    # Other Utility Methods
    def get_notifications(self):
        return test_notifier.NOTIFICATIONS

    def reset_notifications(self):
        test_notifier.NOTIFICATIONS = []

    # Service Methods
    def get_agent_service(self):
        return agent_service.Service()

    def get_api_service(self):
        return api_service.Service()

    def get_central_service(self):
        return central_service.Service()

    def get_sink_service(self):
        return sink_service.Service()

    # Context Methods
    def get_context(self, **kwargs):
        return DesignateContext(**kwargs)

    def get_admin_context(self):
        return DesignateContext.get_admin_context()

    # Fixture methods
    def get_quota_fixture(self, fixture=0, values={}):
        _values = copy.copy(self.quota_fixtures[fixture])
        _values.update(values)
        return _values

    def get_server_fixture(self, fixture=0, values={}):
        _values = copy.copy(self.server_fixtures[fixture])
        _values.update(values)
        return _values

    def get_tsigkey_fixture(self, fixture=0, values={}):
        _values = copy.copy(self.tsigkey_fixtures[fixture])
        _values.update(values)
        return _values

    def get_domain_fixture(self, fixture=0, values={}):
        _values = copy.copy(self.domain_fixtures[fixture])
        _values.update(values)
        return _values

    def get_record_fixture(self, domain_name, fixture=0, values={}):
        _values = copy.copy(self.record_fixtures[fixture])
        _values.update(values)

        try:
            _values['name'] = _values['name'] % domain_name
        except TypeError:
            pass

        return _values

    def get_zonefile_fixture(self, variant=None):
        if variant is None:
            path = 'example.com.zone'
        else:
            path = '%s_example.com.zone' % variant
        path = os.path.join(os.path.dirname(__file__), path)
        with open(path) as zonefile:
            return zonefile.read()

    def create_quota(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        fixture = kwargs.pop('fixture', 0)

        values = self.get_quota_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_quota(context, values=values)

    def create_server(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        fixture = kwargs.pop('fixture', 0)

        values = self.get_server_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_server(context, values=values)

    def create_tsigkey(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        fixture = kwargs.pop('fixture', 0)

        values = self.get_tsigkey_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_tsigkey(context, values=values)

    def create_domain(self, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        fixture = kwargs.pop('fixture', 0)

        # We always need a server to create a domain..
        try:
            self.create_server()
        except exceptions.DuplicateServer:
            pass

        values = self.get_domain_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_domain(context, values=values)

    def create_record(self, domain, **kwargs):
        context = kwargs.pop('context', self.get_admin_context())
        fixture = kwargs.pop('fixture', 0)

        values = self.get_record_fixture(domain['name'], fixture=fixture,
                                         values=kwargs)
        return self.central_service.create_record(context, domain['id'],
                                                  values=values)
