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
import functools
import os
import inspect
import shutil
import tempfile

import fixtures
from oslotest import base
from oslo.config import cfg
from oslo.messaging import conffixture as messaging_fixture
from oslo.messaging.notify import _impl_test as test_notifier
from testtools import testcase

from designate.openstack.common import log as logging
from designate.openstack.common.fixture import config as cfg_fixture
from designate.openstack.common import importutils
from designate import policy
from designate import utils
from designate.context import DesignateContext
from designate.tests import resources
from designate import exceptions
from designate.network_api import fake as fake_network_api
from designate import network_api
from designate import objects
from designate.manage import database as manage_database
from designate.sqlalchemy import utils as sqlalchemy_utils

LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('storage_driver', 'designate.central',
                    group='service:central')
cfg.CONF.import_opt('backend_driver', 'designate.agent',
                    group='service:agent')
cfg.CONF.import_opt('auth_strategy', 'designate.api',
                    group='service:api')
cfg.CONF.import_opt('connection', 'designate.storage.impl_sqlalchemy',
                    group='storage:sqlalchemy')


class NotifierFixture(fixtures.Fixture):
    def setUp(self):
        super(NotifierFixture, self).setUp()
        self.addCleanup(test_notifier.reset)

    def get(self):
        return test_notifier.NOTIFICATIONS

    def clear(self):
        return test_notifier.reset()


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


class TestCase(base.BaseTestCase):
    quota_fixtures = [{
        'resource': 'domains',
        'hard_limit': 5,
    }, {
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

    # The last tld is invalid
    tld_fixtures = [{
        'name': 'com',
    }, {
        'name': 'co.uk',
    }, {
        'name': 'com.',
    }]

    default_tld_fixtures = [{
        'name': 'com',
    }, {
        'name': 'org',
    }, {
        'name': 'net',
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

    # The last domain is invalid
    domain_fixtures = [{
        'name': 'example.com.',
        'email': 'example@example.com',
    }, {
        'name': 'example.net.',
        'email': 'example@example.net',
    }, {
        'name': 'example.org.',
        'email': 'example@example.org',
    }, {
        'name': 'invalid.com.....',
        'email': 'example@invalid.com',
    }]

    recordset_fixtures = {
        'A': [
            {'name': 'mail.%s', 'type': 'A'},
            {'name': 'www.%s', 'type': 'A'},
        ],
        'MX': [
            {'name': 'mail.%s', 'type': 'MX'},
        ],
        'SRV': [
            {'name': '_sip._tcp.%s', 'type': 'SRV'},
            {'name': '_sip._udp.%s', 'type': 'SRV'},
        ],
        'CNAME': [
            {'name': 'www.%s', 'type': 'CNAME'},
            {'name': 'sub1.%s', 'type': 'CNAME'},
        ]
    }

    record_fixtures = {
        'A': [
            {'data': '192.0.2.1'},
            {'data': '192.0.2.2'}
        ],
        'MX': [
            {'data': 'mail.example.org.', 'priority': 5},
            {'data': 'mail.example.com.', 'priority': 10},
        ],
        'SRV': [
            {'data': '0 5060 server1.example.org.', 'priority': 5},
            {'data': '1 5060 server2.example.org.', 'priority': 10},
        ],
        'CNAME': [
            {'data': 'www.somedomain.org.'},
            {'data': 'www.someotherdomain.com.'},
        ]
    }

    ptr_fixtures = [
        {'ptrdname': 'srv1.example.com.'},
        {'ptrdname': 'srv1.example.net.'}
    ]

    blacklist_fixtures = [{
        'pattern': 'blacklisted.com.',
        'description': 'This is a comment',
    }, {
        'pattern': 'blacklisted.net.'
    }, {
        'pattern': 'blacklisted.org.'
    }]

    def setUp(self):
        super(TestCase, self).setUp()

        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf

        self.messaging_conf = self.useFixture(
            messaging_fixture.ConfFixture(cfg.CONF))
        self.messaging_conf.transport_driver = 'fake'

        self.config(notification_driver='test')

        self.notifications = self.useFixture(NotifierFixture())

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

        # The database fixture needs to be set up here (as opposed to isolated
        # in a storage test case) because many tests end up using storage.
        REPOSITORY = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  '..', 'storage',
                                                  'impl_sqlalchemy',
                                                  'migrate_repo'))
        self.db_fixture = self.useFixture(
            DatabaseFixture.get_fixture(
                REPOSITORY, manage_database.INIT_VERSION))
        self.config(
            connection=self.db_fixture.url,
            connection_debug=100,
            group='storage:sqlalchemy'
        )

        self.config(network_api='fake')
        self.config(
            managed_resource_tenant_id='managing_tenant',
            group='service:central')

        # "Read" Configuration
        self.CONF([], project='designate')

        self.useFixture(PolicyFixture())
        self.network_api = NetworkAPIFixture()
        self.useFixture(self.network_api)
        self.central_service = self.start_service('central')

        self.admin_context = self.get_admin_context()

    # Config Methods
    def config(self, **kwargs):
        group = kwargs.pop('group', None)

        for k, v in kwargs.iteritems():
            cfg.CONF.set_override(k, v, group)

    def policy(self, rules, default_rule='allow', overwrite=True):
        # Inject an allow and deny rule
        rules['allow'] = '@'
        rules['deny'] = '!'

        # Set the rules
        policy.set_rules(rules, default_rule, overwrite)

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
            tenant=utils.generate_uuid(),
            user=utils.generate_uuid())

    # Fixture methods
    def get_quota_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.quota_fixtures[fixture])
        _values.update(values)
        return _values

    def get_server_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.server_fixtures[fixture])
        _values.update(values)
        return _values

    def get_tld_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.tld_fixtures[fixture])
        _values.update(values)
        return _values

    def get_default_tld_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.default_tld_fixtures[fixture])
        _values.update(values)
        return _values

    def get_tsigkey_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.tsigkey_fixtures[fixture])
        _values.update(values)
        return _values

    def get_domain_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.domain_fixtures[fixture])
        _values.update(values)
        return _values

    def get_recordset_fixture(self, domain_name, type='A', fixture=0,
                              values=None):
        values = values or {}

        _values = copy.copy(self.recordset_fixtures[type][fixture])
        _values.update(values)

        try:
            _values['name'] = _values['name'] % domain_name
        except TypeError:
            pass

        return _values

    def get_record_fixture(self, recordset_type, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.record_fixtures[recordset_type][fixture])
        _values.update(values)
        return _values

    def get_ptr_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.ptr_fixtures[fixture])
        _values.update(values)
        return _values

    def get_zonefile_fixture(self, variant=None):
        if variant is None:
            f = 'example.com.zone'
        else:
            f = '%s_example.com.zone' % variant
        path = os.path.join(resources.path, 'zonefiles', f)
        with open(path) as zonefile:
            return zonefile.read()

    def get_blacklist_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.blacklist_fixtures[fixture])
        _values.update(values)
        return _values

    def create_server(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_server_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_server(
            context, objects.Server(**values))

    def create_tld(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_tld_fixture(fixture=fixture, values=kwargs)
        tld = objects.Tld(**values)
        return self.central_service.create_tld(context, tld=tld)

    def create_default_tld(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_default_tld_fixture(fixture=fixture, values=kwargs)
        tld = objects.Tld(**values)
        return self.central_service.create_tld(context, tld=tld)

    def create_default_tlds(self):
        for index in range(len(self.default_tld_fixtures)):
            try:
                self.create_default_tld(fixture=index)
            except exceptions.DuplicateTld:
                pass

    def create_tsigkey(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_tsigkey_fixture(fixture=fixture, values=kwargs)
        return self.central_service.create_tsigkey(
            context, objects.TsigKey(**values))

    def create_domain(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        try:
            # We always need a server to create a domain..
            self.create_server()
        except exceptions.DuplicateServer:
            pass

        values = self.get_domain_fixture(fixture=fixture, values=kwargs)

        if 'tenant_id' not in values:
            values['tenant_id'] = context.tenant

        return self.central_service.create_domain(
            context, objects.Domain(**values))

    def create_recordset(self, domain, type='A', **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_recordset_fixture(domain['name'], type=type,
                                            fixture=fixture,
                                            values=kwargs)
        return self.central_service.create_recordset(
            context, domain['id'], recordset=objects.RecordSet(**values))

    def create_record(self, domain, recordset, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_record_fixture(recordset['type'], fixture=fixture,
                                         values=kwargs)
        return self.central_service.create_record(
            context,
            domain['id'],
            recordset['id'],
            record=objects.Record(**values))

    def create_blacklist(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_blacklist_fixture(fixture=fixture, values=kwargs)
        blacklist = objects.Blacklist(**values)
        return self.central_service.create_blacklist(
            context, blacklist=blacklist)

    def _ensure_interface(self, interface, implementation):
        for name in interface.__abstractmethods__:
            in_arginfo = inspect.getargspec(getattr(interface, name))
            im_arginfo = inspect.getargspec(getattr(implementation, name))

            self.assertEqual(
                in_arginfo, im_arginfo,
                "Method Signature for '%s' mismatched" % name)


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
