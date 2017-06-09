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
import inspect
import os
import time

from testtools import testcase
from oslotest import base
from oslo_log import log as logging
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
from oslo_messaging import conffixture as messaging_fixture

from designate import policy
from designate import utils
from designate import exceptions
from designate import objects
from designate import storage
from designate.context import DesignateContext
from designate.tests import fixtures
from designate.tests import resources
from designate.manage import database as manage_database

import eventlet

eventlet.monkey_patch(os=False)


LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('storage_driver', 'designate.central',
                    group='service:central')
cfg.CONF.import_opt('auth_strategy', 'designate.api',
                    group='service:api')
cfg.CONF.import_opt('connection', 'designate.storage.impl_sqlalchemy',
                    group='storage:sqlalchemy')
cfg.CONF.import_opt('cache_driver', 'designate.pool_manager',
                    group='service:pool_manager')
cfg.CONF.import_opt('connection',
                    'designate.pool_manager.cache.impl_sqlalchemy',
                    group='pool_manager_cache:sqlalchemy')
cfg.CONF.import_opt('emitter_type', 'designate.service_status',
                    group="heartbeat_emitter")
cfg.CONF.import_opt('scheduler_filters', 'designate.scheduler',
                    group="service:central")
default_pool_id = cfg.CONF['service:central'].default_pool_id

_TRUE_VALUES = ('true', '1', 'yes', 'y')


class TestTimeoutError(Exception):
    # Used in wait_for_condition
    pass


class TestCase(base.BaseTestCase):
    service_status_fixtures = [{
        'service_name': 'foo',
        'hostname': 'bar',
        'status': "UP",
        'stats': {},
        'capabilities': {},
    }]

    quota_fixtures = [{
        'resource': 'zones',
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
        'scope': 'POOL',
        'resource_id': '6ca6baef-3305-4ad0-a52b-a82df5752b62',
    }, {
        'name': 'test-key-two',
        'algorithm': 'hmac-sha256',
        'secret': 'AnotherSecretKey',
        'scope': 'ZONE',
        'resource_id': '7fbb6304-5e74-4691-bd80-cef3cff5fe2f',
    }]

    # The last zone is invalid
    zone_fixtures = {
        'PRIMARY': [
            {
                'name': 'example.com.',
                'type': 'PRIMARY',
                'email': 'example@example.com',
            }, {
                'name': 'example.net.',
                'type': 'PRIMARY',
                'email': 'example@example.net',
            }, {
                'name': 'example.org.',
                'type': 'PRIMARY',
                'email': 'example@example.org',
            }, {
                'name': 'invalid.com.....',
                'type': 'PRIMARY',
                'email': 'example@invalid.com',
            }
        ],
        'SECONDARY': [
            {
                'name': 'example.com.',
                'type': 'SECONDARY',
            }, {
                'name': 'example.net.',
                'type': 'SECONDARY',
            }, {
                'name': 'example.org.',
                'type': 'SECONDARY',
            }, {
                'name': 'invalid.com.....',
                'type': 'SECONDARY',
            }
        ]

    }

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
        'TXT': [
            {'name': 'text.%s', 'type': 'TXT'},
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
            {'data': '5 mail.example.org.'},
            {'data': '10 mail.example.com.'},
        ],
        'SRV': [
            {'data': '5 0 5060 server1.example.org.'},
            {'data': '10 1 5060 server2.example.org.'},
        ],
        'CNAME': [
            {'data': 'www.somezone.org.'},
            {'data': 'www.someotherzone.com.'},
        ],
        'TXT': [
            {'data': 'footxtdata'}
        ]
    }

    ptr_fixtures = [
        {'ptrdname': 'srv1.example.com.'},
        {'ptrdname': 'srv1.example.net.'}
    ]

    blacklist_fixtures = [{
        'pattern': 'blacklisted.com.',
        'description': u'This is a comment',
    }, {
        'pattern': 'blacklisted.net.'
    }, {
        'pattern': 'blacklisted.org.'
    }]

    pool_fixtures = [
        {'name': 'Pool-One',
         'description': u'Pool-One description',
         'attributes': [{'key': 'scope', 'value': 'public'}],
         'ns_records': [{'priority': 1, 'hostname': 'ns1.example.org.'},
                        {'priority': 2, 'hostname': 'ns2.example.org.'}]},

        {'name': 'Pool-Two',
         'description': u'Pool-Two description',
         'attributes': [{'key': 'scope', 'value': 'public'}],
         'ns_records': [{'priority': 1, 'hostname': 'ns1.example.org.'}]},
    ]

    pool_attribute_fixtures = [
        {'scope': 'public'},
        {'scope': 'private'},
        {'scope': 'unknown'}
    ]

    pool_attributes_fixtures = [
        {'pool_id': default_pool_id,
         'key': 'continent',
         'value': 'NA'},
        {'pool_id': default_pool_id,
         'key': 'scope',
         'value': 'public'}
    ]

    pool_nameserver_fixtures = [
        {'pool_id': default_pool_id,
         'host': "192.0.2.1",
         'port': 53},
        {'pool_id': default_pool_id,
         'host': "192.0.2.2",
         'port': 53},
    ]

    pool_target_fixtures = [
        {'pool_id': default_pool_id,
         'type': "fake",
         'description': u"FooBar"},
        {'pool_id': default_pool_id,
         'type': "fake",
         'description': u"BarFoo"},
    ]

    pool_also_notify_fixtures = [
        {'pool_id': default_pool_id,
         'host': "192.0.2.1",
         'port': 53},
        {'pool_id': default_pool_id,
         'host': "192.0.2.2",
         'port': 53},
    ]

    zone_transfers_request_fixtures = [{
        "description": "Test Transfer",
    }, {
        "description": "Test Transfer 2 - with target",
        "target_tenant_id": "target_tenant_id"
    }]

    zone_import_fixtures = [{
        'status': 'PENDING',
        'zone_id': None,
        'message': None,
        'task_type': 'IMPORT'
    }, {
        'status': 'ERROR',
        'zone_id': None,
        'message': None,
        'task_type': 'IMPORT'
    }, {
        'status': 'COMPLETE',
        'zone_id': '6ca6baef-3305-4ad0-a52b-a82df5752b62',
        'message': None,
        'task_type': 'IMPORT'
    }]

    zone_export_fixtures = [{
        'status': 'PENDING',
        'zone_id': None,
        'message': None,
        'task_type': 'EXPORT'
    }, {
        'status': 'ERROR',
        'zone_id': None,
        'message': None,
        'task_type': 'EXPORT'
    }, {
        'status': 'COMPLETE',
        'zone_id': '6ca6baef-3305-4ad0-a52b-a82df5752b62',
        'message': None,
        'task_type': 'EXPORT'
    }]

    def setUp(self):
        super(TestCase, self).setUp()

        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf

        self.messaging_conf = messaging_fixture.ConfFixture(cfg.CONF)
        self.messaging_conf.transport_driver = 'fake'
        self.messaging_conf.response_timeout = 5
        self.useFixture(self.messaging_conf)

        self.config(notification_driver=['test'])

        self.useFixture(fixtures.RPCFixture(cfg.CONF))

        self.config(
            storage_driver='sqlalchemy',
            group='service:central'
        )

        self.config(
            emitter_type="noop",
            group="heartbeat_emitter"
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
            fixtures.DatabaseFixture.get_fixture(
                REPOSITORY, manage_database.INIT_VERSION))

        if os.getenv('DESIGNATE_SQL_DEBUG', "False").lower() in _TRUE_VALUES:
            connection_debug = 50
        else:
            connection_debug = 0

        self.config(
            connection=self.db_fixture.url,
            connection_debug=connection_debug,
            group='storage:sqlalchemy'
        )

        self._setup_pool_manager_cache()

        self.config(network_api='fake')

        self.config(
            scheduler_filters=['pool_id_attribute', 'random'],
            group='service:central')

        # "Read" Configuration
        self.CONF([], project='designate')
        utils.register_plugin_opts()

        self.useFixture(fixtures.PolicyFixture())
        self.network_api = fixtures.NetworkAPIFixture()
        self.useFixture(self.network_api)
        self.central_service = self.start_service('central')

        self.admin_context = self.get_admin_context()
        storage_driver = cfg.CONF['service:central'].storage_driver
        self.storage = storage.get_storage(storage_driver)

        # Setup the Default Pool with some useful settings
        self._setup_default_pool()

    def _setup_pool_manager_cache(self):

        self.config(
            cache_driver='sqlalchemy',
            group='service:pool_manager')

        repository = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  '..',
                                                  'pool_manager',
                                                  'cache',
                                                  'impl_sqlalchemy',
                                                  'migrate_repo'))
        db_fixture = self.useFixture(
            fixtures.DatabaseFixture.get_fixture(repository))

        if os.getenv('DESIGNATE_SQL_DEBUG', "False").lower() in _TRUE_VALUES:
            connection_debug = 50
        else:
            connection_debug = 0

        self.config(
            connection=db_fixture.url,
            connection_debug=connection_debug,
            group='pool_manager_cache:sqlalchemy')

    def _setup_default_pool(self):
        # Fetch the default pool
        pool = self.storage.get_pool(self.admin_context, default_pool_id)

        # Fill out the necessary pool details
        pool.ns_records = objects.PoolNsRecordList.from_list([
            {'hostname': 'ns1.example.org.', 'priority': 1}
        ])

        pool.targets = objects.PoolTargetList.from_list([
            {'type': 'fake', u'description': u"Fake PoolTarget for Tests"}
        ])

        # Save the default pool
        self.storage.update_pool(self.admin_context, pool)

    # Config Methods
    def config(self, **kwargs):
        group = kwargs.pop('group', None)

        for k, v in kwargs.items():
            cfg.CONF.set_override(k, v, group)

    def policy(self, rules, default_rule='allow', overwrite=True):
        # Inject an allow and deny rule
        rules['allow'] = '@'
        rules['deny'] = '!'

        # Set the rules
        policy.set_rules(rules, default_rule, overwrite)

    def start_service(self, svc_name, *args, **kw):
        """
        Convenience method for starting a service!
        """
        fixture = fixtures.ServiceFixture(svc_name, *args, **kw)
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

    def get_zone_fixture(self, zone_type=None, fixture=0, values=None):
        zone_type = zone_type or 'PRIMARY'

        _values = copy.copy(self.zone_fixtures[zone_type][fixture])
        if values:
            _values.update(values)

        return _values

    def get_recordset_fixture(self, zone_name, type='A', fixture=0,
                              values=None):
        values = values or {}

        _values = copy.copy(self.recordset_fixtures[type][fixture])
        _values.update(values)

        try:
            _values['name'] = _values['name'] % zone_name
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
        return objects.FloatingIP().from_dict(_values)

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

    def get_pool_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.pool_fixtures[fixture])
        _values.update(values)
        return _values

    def get_pool_attribute_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.pool_attribute_fixtures[fixture])
        _values.update(values)
        return _values

    def get_pool_attributes_fixture(self, fixture=0, values=None):
        # TODO(kiall): Remove this method, in favor of the
        #              get_pool_attribute_fixture method above.
        values = values or {}

        _values = copy.copy(self.pool_attributes_fixtures[fixture])
        _values.update(values)
        return _values

    def get_pool_nameserver_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.pool_nameserver_fixtures[fixture])
        _values.update(values)
        return _values

    def get_pool_target_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.pool_target_fixtures[fixture])
        _values.update(values)
        return _values

    def get_pool_also_notify_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.pool_also_notify_fixtures[fixture])
        _values.update(values)
        return _values

    def get_zone_transfer_request_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.zone_transfers_request_fixtures[fixture])
        _values.update(values)
        return _values

    def get_zone_transfer_accept_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.zone_transfers_accept_fixtures[fixture])
        _values.update(values)
        return _values

    def get_zone_import_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.zone_import_fixtures[fixture])
        _values.update(values)
        return _values

    def get_zone_export_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.zone_export_fixtures[fixture])
        _values.update(values)
        return _values

    def get_service_status_fixture(self, fixture=0, values=None):
        values = values or {}

        _values = copy.copy(self.service_status_fixtures[fixture])
        _values.update(values)
        return _values

    def update_service_status(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_service_status_fixture(
            fixture=fixture, values=kwargs)

        return self.central_service.update_service_status(
            context, objects.ServiceStatus.from_dict(values))

    def create_tld(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_tld_fixture(fixture=fixture, values=kwargs)

        return self.central_service.create_tld(
            context, objects.Tld.from_dict(values))

    def create_default_tld(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_default_tld_fixture(fixture=fixture, values=kwargs)

        return self.central_service.create_tld(
            context, objects.Tld.from_dict(values))

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
            context, objects.TsigKey.from_dict(values))

    def create_zone(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)
        zone_type = kwargs.pop('type', None)

        values = self.get_zone_fixture(zone_type=zone_type,
                                       fixture=fixture, values=kwargs)

        if 'tenant_id' not in values:
            values['tenant_id'] = context.tenant

        return self.central_service.create_zone(
            context, objects.Zone.from_dict(values))

    def create_recordset(self, zone, type='A', increment_serial=True,
                         **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_recordset_fixture(zone['name'], type=type,
                                            fixture=fixture,
                                            values=kwargs)

        return self.central_service.create_recordset(
            context, zone['id'], objects.RecordSet.from_dict(values),
            increment_serial=increment_serial)

    def create_record(self, zone, recordset, increment_serial=True,
                      **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_record_fixture(recordset['type'], fixture=fixture,
                                         values=kwargs)

        return self.central_service.create_record(
            context, zone['id'], recordset['id'],
            objects.Record.from_dict(values),
            increment_serial=increment_serial)

    def create_blacklist(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_blacklist_fixture(fixture=fixture, values=kwargs)

        return self.central_service.create_blacklist(
            context, objects.Blacklist.from_dict(values))

    def create_pool(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_pool_fixture(fixture=fixture, values=kwargs)

        if 'tenant_id' not in values:
            values['tenant_id'] = context.tenant

        return self.central_service.create_pool(
            context, objects.Pool.from_dict(values))

    def create_pool_attribute(self, **kwargs):
        # TODO(kiall): This method should require a "pool" be passed in,
        #              rather than hardcoding the default pool ID into the
        #              fixture.
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_pool_attributes_fixture(fixture=fixture,
                                                  values=kwargs)

        # TODO(kiall): We shouldn't be assuming the default_pool_id here
        return self.storage.create_pool_attribute(
            context, default_pool_id,
            objects.PoolAttribute.from_dict(values))

    def create_zone_transfer_request(self, zone, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_zone_transfer_request_fixture(
            fixture=fixture, values=kwargs)

        if 'zone_id' not in values:
            values['zone_id'] = zone.id

        return self.central_service.create_zone_transfer_request(
            context, objects.ZoneTransferRequest.from_dict(values))

    def create_zone_transfer_accept(self, zone_transfer_request, **kwargs):
        context = kwargs.pop('context', self.admin_context)

        values = {}

        if 'tenant_id' not in values:
            values['tenant_id'] = context.tenant

        if 'zone_transfer_request_id' not in values:
            values['zone_transfer_request_id'] = zone_transfer_request.id

        if 'zone_id' not in values:
            values['zone_id'] = zone_transfer_request.zone_id

        if 'key' not in values:
            values['key'] = zone_transfer_request.key

        return self.central_service.create_zone_transfer_accept(
            context, objects.ZoneTransferAccept.from_dict(values))

    def create_zone_import(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        zone_import = self.get_zone_import_fixture(fixture=fixture,
                                               values=kwargs)

        return self.storage.create_zone_import(
            context, objects.ZoneImport.from_dict(zone_import))

    def create_zone_export(self, **kwargs):
        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        zone_export = self.get_zone_export_fixture(fixture=fixture,
                                               values=kwargs)

        return self.storage.create_zone_export(
            context, objects.ZoneExport.from_dict(zone_export))

    def wait_for_import(self, zone_import_id, errorok=False):
        """
           Zone imports spawn a thread to parse the zone file and
           insert the data. This waits for this process before continuing
        """
        attempts = 0
        while attempts < 20:
            # Give the import a half second to complete
            time.sleep(.5)

            # Retrieve it, and ensure it's the same
            zone_import = self.central_service.get_zone_import(
                self.admin_context, zone_import_id)

            # If the import is done, we're done
            if zone_import.status == 'COMPLETE':
                break

            # If errors are allowed, just make sure that something completed
            if errorok:
                if zone_import.status != 'PENDING':
                    break

            attempts += 1

        if not errorok:
            self.assertEqual('COMPLETE', zone_import.status)

    def _ensure_interface(self, interface, implementation):
        for name in interface.__abstractmethods__:
            in_arginfo = inspect.getargspec(getattr(interface, name))
            im_arginfo = inspect.getargspec(getattr(implementation, name))

            self.assertEqual(
                in_arginfo, im_arginfo,
                "Method Signature for '%s' mismatched" % name)

    def wait_for_condition(self, condition, interval=0.3, timeout=2):
        """Wait for a condition to be true or raise an exception after
        `timeout` seconds.
        Poll every `interval` seconds.  `condition` can be a callable.
        (Caution: some mocks behave both as values and callables.)
        """
        t_max = time.time() + timeout
        while time.time() < t_max:
            if callable(condition):
                result = condition()
            else:
                result = condition

            if result:
                return result

            time.sleep(interval)

        raise TestTimeoutError


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
