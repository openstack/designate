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
from moniker.openstack.common import cfg
from moniker.openstack.common import policy
from moniker.openstack.common import log as logging
from moniker.context import MonikerContext
from moniker import storage
from moniker import exceptions
from moniker.agent import service as agent_service
from moniker.api import service as api_service
from moniker.central import service as central_service
from moniker.sink import service as sink_service

LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('storage_driver', 'moniker.central',
                    group='service:central')
cfg.CONF.import_opt('backend_driver', 'moniker.agent',
                    group='service:agent')
cfg.CONF.import_opt('auth_strategy', 'moniker.api',
                    group='service:api')
cfg.CONF.import_opt('database_connection', 'moniker.storage.impl_sqlalchemy',
                    group='storage:sqlalchemy')


class AssertMixin(object):
    """
    Mixin to hold assert helpers.

    """
    def assertLen(self, expected_length, obj):
        """
        Assert a length of a object

        :param obj: The object ot run len() on
        :param expected_length: The length in Int that's expected from len(obj)
        """
        self.assertEqual(len(obj), expected_length)

    def assertData(self, expected_data, data):
        """
        A simple helper to very that at least fixture data is the same
        as returned

        :param expected_data: Data that's expected
        :param data: Data to check expected_data against
        """
        for key, value in expected_data.items():
            self.assertEqual(data[key], value)

    def assertResponse(self, expected_data, data, schema=None):
        """
        If passed schema, do schema.validate() on data and pass
        expected_data + data to self.assertData()

        :param schema: A schema to validate data with
        """
        if schema:
            schema.validate(data)
        self.assertData(expected_data, data)


class TestCase(unittest2.TestCase, AssertMixin):
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
    }]

    record_fixtures = [
        {'name': 'www.%s', 'type': 'A', 'data': '192.0.2.1'},
        {'name': 'mail.%s', 'type': 'A', 'data': '192.0.2.2'}
    ]

    def setUp(self):
        super(TestCase, self).setUp()

        self.mox = mox.Mox()

        self.config(
            notification_driver=[],
            rpc_backend='moniker.openstack.common.rpc.impl_fake',
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
            api_paste_config='api-paste.ini.sample',
            group='service:api'
        )

        self.config(
            database_connection='sqlite://',
            group='storage:sqlalchemy'
        )

        storage.setup_schema()

        self.admin_context = self.get_admin_context()

    def tearDown(self):
        policy.reset()
        storage.teardown_schema()
        cfg.CONF.reset()
        self.mox.UnsetStubs()
        super(TestCase, self).tearDown()

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
        return MonikerContext(**kwargs)

    def get_admin_context(self):
        return MonikerContext.get_admin_context()

    # Fixture methods
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
