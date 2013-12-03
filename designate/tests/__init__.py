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
import fixtures
import functools
import os
from testtools import testcase
from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.openstack.common.notifier import test_notifier
from designate.openstack.common.fixture import config
from designate.openstack.common import importutils
from designate.openstack.common import policy
from designate.openstack.common import test
from designate.openstack.common import uuidutils
from designate.context import DesignateContext
from designate.tests import resources
from designate import storage
from designate import exceptions

LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('storage_driver', 'designate.central',
                    group='service:central')
cfg.CONF.import_opt('backend_driver', 'designate.agent',
                    group='service:agent')
cfg.CONF.import_opt('auth_strategy', 'designate.api',
                    group='service:api')
cfg.CONF.import_opt('database_connection', 'designate.storage.impl_sqlalchemy',
                    group='storage:sqlalchemy')
# NOTE: Since we're importing service classes in start_service this breaks
# if not here.
cfg.CONF.import_opt(
    'notification_driver', 'designate.openstack.common.notifier.api')


class StorageFixture(fixtures.Fixture):
    def setUp(self):
        super(StorageFixture, self).setUp()
        self.storage = storage.get_storage()
        self.storage.setup_schema()
        self.addCleanup(self.storage.teardown_schema)


class NotifierFixture(fixtures.Fixture):
    def setUp(self):
        super(NotifierFixture, self).setUp()
        self.addCleanup(self.clear)

    def get(self):
        return test_notifier.NOTIFICATIONS

    def clear(self):
        test_notifier.NOTIFICATIONS = []


class ServiceFixture(fixtures.Fixture):
    def __init__(self, svc_name, *args, **kw):
        cls = importutils.import_class(
            'designate.%s.service.Service' % svc_name)
        self.svc = cls(*args, **kw)

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


class TestCase(test.BaseTestCase):
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

        self.useFixture(fixtures.FakeLogger('designate', level='DEBUG'))
        self.CONF = self.useFixture(config.Config(cfg.CONF)).conf

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

        self.CONF([], project='designate')

        self.notifications = NotifierFixture()
        self.useFixture(self.notifications)

        storage_fixture = StorageFixture()
        self.useFixture(storage_fixture)

        self.useFixture(PolicyFixture())

        self.admin_context = self.get_admin_context()

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
        return self.notifications.get()

    def reset_notifications(self):
        self.notifications.clear()

    def start_service(self, svc_name, *args, **kw):
        """
        Convenience method for starting a service!
        """
        fixture = ServiceFixture(svc_name, *args, **kw)
        self.useFixture(fixture)
        return fixture.svc

    # Context Methods
    def get_context(self, **kwargs):
        return DesignateContext(**kwargs)

    def get_admin_context(self):
        return DesignateContext.get_admin_context(
            tenant=uuidutils.generate_uuid(),
            user=uuidutils.generate_uuid())

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
            f = 'example.com.zone'
        else:
            f = '%s_example.com.zone' % variant
        path = os.path.join(resources.path, 'zonefiles', f)
        with open(path) as zonefile:
            return zonefile.read()

    def create_quota(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_quota_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_quota(context, values=values)

    def create_server(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_server_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_server(context, values=values)

    def create_tsigkey(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_tsigkey_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_tsigkey(context, values=values)

    def create_domain(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        # We always need a server to create a domain..
        try:
            self.create_server()
        except exceptions.DuplicateServer:
            pass

        values = self.get_domain_fixture(fixture=fixture, values=kwargs)

        if 'tenant_id' not in values:
            values['tenant_id'] = context.tenant_id

        return self.central_service.create_domain(context, values=values)

    def create_record(self, domain, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_record_fixture(domain['name'], fixture=fixture,
                                         values=kwargs)
        return self.central_service.create_record(context, domain['id'],
                                                  values=values)


def _skip_decorator(func):
    @functools.wraps(func)
    def skip_if_not_implemented(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NotImplementedError as e:
            raise testcase.TestSkipped(str(e))
        except Exception as e:
            if 'not implemented' in str(e):
                raise testcase.TestSkipped(str(e))
            raise
    return skip_if_not_implemented


class SkipNotImplementedMeta(type):
    def __new__(cls, name, bases, local):
        for attr in local:
            value = local[attr]
            if callable(value) and (
                    attr.startswith('test_') or attr == 'setUp'):
                local[attr] = _skip_decorator(value)
        return type.__new__(cls, name, bases, local)
