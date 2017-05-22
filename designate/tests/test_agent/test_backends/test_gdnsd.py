# Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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

"""
    Functional-test the Gdnsd 2 agent backend

    These tests rely on creating directories and files and running
    gdnsd.
    gdnsd must be installed
"""

from textwrap import dedent as de
import glob
import os
import tempfile
import unittest

from oslo_concurrency.processutils import ProcessExecutionError
from oslo_config import cfg
from oslo_config import fixture as cfg_fixture
import dns
import fixtures
import mock
import testtools

from designate import exceptions
from designate.backend.agent_backend.impl_gdnsd import CFG_GROUP
from designate.backend.agent_backend.impl_gdnsd import GdnsdBackend
from designate.tests import TestCase

TMPFS_DIR = "/dev/shm"
ROOT_TMP_DIR = TMPFS_DIR if os.path.isdir(TMPFS_DIR) else "/tmp"
GDNSD_BIN_PATH = "/usr/sbin/gdnsd"
GDNSD_NOT_AVAILABLE = not os.path.isfile(GDNSD_BIN_PATH)

ZONE_TPL = """
$ORIGIN %(name)s
%(name)s 3600 IN SOA ns.%(name)s email.%(name)s. 1421777854 3600 600 86400 3600
%(name)s 3600 IN NS ns.%(name)s
ns 300 IN A 127.0.0.1
"""  # noqa


class GdnsdAgentBackendTestCase(TestCase):

    def setUp(self):
        super(GdnsdAgentBackendTestCase, self).setUp()
        self.conf_dir_path = tempfile.mkdtemp(dir=ROOT_TMP_DIR)
        self.zones_dir_path = os.path.join(self.conf_dir_path, 'zones')
        os.mkdir(self.zones_dir_path)
        self.CONF = self.useFixture(cfg_fixture.Config(cfg.CONF)).conf
        cfg.CONF.set_override('confdir_path', self.conf_dir_path, CFG_GROUP)
        cfg.CONF.set_override('gdnsd_cmd_name', GDNSD_BIN_PATH, CFG_GROUP)

        self.backend = GdnsdBackend('foo')

    def tearDown(self):
        super(GdnsdAgentBackendTestCase, self).tearDown()
        for zone_fn in glob.glob(os.path.join(self.zones_dir_path, "*.org")):
            os.remove(zone_fn)
        os.rmdir(self.zones_dir_path)
        os.rmdir(self.conf_dir_path)

    def _patch_ob(self, *a, **kw):
                self.useFixture(fixtures.MockPatchObject(*a, **kw))

    def _create_dnspy_zone(self, name):
        name = name.rstrip('.')
        zone_text = ZONE_TPL % {'name': name}
        return dns.zone.from_text(zone_text, check_origin=False)

    def _create_dnspy_zone_with_records(self, name):
        zone_text = (
            '$ORIGIN %(name)s\n'
            '@  3600 IN SOA %(ns)s email.%(name)s 1421777854 3600 600 86400 3600\n'  # noqa
            '   3600 IN NS %(ns)s\n'
            '   1800 IN A 173.194.123.30\n'
            '   1800 IN A 173.194.123.31\n'
            's  2400 IN AAAA 2001:db8:cafe::1\n'
            's  2400 IN AAAA 2001:db8:cafe::2\n'
            % {'name': name, 'ns': 'ns1.example.net.'}
        )
        return dns.zone.from_text(zone_text, check_origin=False)

    @mock.patch('designate.utils.execute', return_value=("", ""))
    def test_start(self, *mocks):
        self.backend.start()

    @mock.patch('designate.utils.execute', side_effect=ProcessExecutionError)
    def test_exec_error(self, *mocks):
        with testtools.ExpectedException(exceptions.Backend):
            self.backend._check_conf()

    def test_create_zone(self, *mocks):
        zone = self._create_dnspy_zone('example.org')
        self.backend.create_zone(zone)

        zone_fn = os.path.join(self.zones_dir_path, "example.org")
        expected = de("""\
            ns 300 IN A 127.0.0.1
            @ 3600 IN SOA ns email.example.org. 1421777854 3600 600 86400 3600
            @ 3600 IN NS ns
        """)
        with open(zone_fn) as f:
            self.assertEqual(expected, f.read())

    @unittest.skipIf(GDNSD_NOT_AVAILABLE, "gdnsd binary not installed")
    def test_create_zone_and_check(self):
        zone = self._create_dnspy_zone('example.org')
        self.backend.create_zone(zone)
        self.backend._check_conf()

    def test_update_zone(self):
        zone = self._create_dnspy_zone_with_records('example.org')
        self.backend.update_zone(zone)

        zone_fn = os.path.join(self.zones_dir_path, "example.org")
        expected = de("""\
            @ 3600 IN SOA ns1.example.net. email 1421777854 3600 600 86400 3600
            @ 3600 IN NS ns1.example.net.
            @ 1800 IN A 173.194.123.30
            @ 1800 IN A 173.194.123.31
            s 2400 IN AAAA 2001:db8:cafe::1
            s 2400 IN AAAA 2001:db8:cafe::2
        """)  # noqa
        with open(zone_fn) as f:
            self.assertEqual(expected, f.read())

    @unittest.skipIf(GDNSD_NOT_AVAILABLE, "gdnsd binary not installed")
    def test_update_zone_and_check(self):
        zone = self._create_dnspy_zone_with_records('example.org')
        self.backend.update_zone(zone)
        self.backend._check_conf()

    def test_delete_zone(self):
        foo_fn = os.path.join(self.zones_dir_path, 'foo')
        with open(foo_fn, 'w') as f:
            f.write("42")
        self.backend.delete_zone('foo')
        self.assertFalse(os.path.isfile(foo_fn))
        self.backend.delete_zone('foo')
