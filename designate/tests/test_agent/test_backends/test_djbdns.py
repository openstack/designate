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
    Test the Djbdns agent backend

    These tests *do* rely on creating directories and files or running
    executables from the djbdns suite

    If djbdns is not available some tests are skipped.
"""

import os
import tempfile
import unittest

import fixtures
import mock

from designate import exceptions
from designate.backend.agent_backend.impl_djbdns import DjbdnsBackend
from designate.tests import TestCase
import designate.backend.agent_backend.impl_djbdns

TINYDNSDATA_PATH = '/usr/bin/tinydns-data'


class DjbdnsAgentBackendSimpleTestCase(TestCase):

    def test__check_dirs(self):
        DjbdnsBackend._check_dirs('/tmp')

    def test__check_dirs_not_found(self):
        self.assertRaises(
            exceptions.Backend,
            DjbdnsBackend._check_dirs,
            '/nonexistent_dir_name'
        )


class DjbdnsAgentBackendTestCase(TestCase):

    def setUp(self):
        super(DjbdnsAgentBackendTestCase, self).setUp()
        self.CONF.set_override('masters', ['127.0.0.1:5354'], 'service:agent')
        tmp_datafiles_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(tmp_datafiles_dir, 'datafiles'))
        self.CONF.set_override(
            'tinydns_datadir',
            tmp_datafiles_dir,
            designate.backend.agent_backend.impl_djbdns.CFG_GROUP
        )
        self.useFixture(fixtures.MockPatchObject(
            DjbdnsBackend, '_check_dirs'
        ))
        self.backend = DjbdnsBackend('foo')
        self.patch_ob(self.backend._resolver, 'query')

    def tearDown(self):
        super(DjbdnsAgentBackendTestCase, self).tearDown()

    def patch_ob(self, *a, **kw):
        self.useFixture(fixtures.MockPatchObject(*a, **kw))

    @mock.patch('designate.backend.agent_backend.impl_djbdns.os.remove')
    @mock.patch('designate.backend.agent_backend.impl_djbdns.execute')
    def test__perform_axfr_from_minidns(self, mock_exe, mock_rm):
        mock_exe.return_value = (None, None)

        self.backend._perform_axfr_from_minidns('foo')

        mock_exe.assert_called_once_with(
            'tcpclient', '127.0.0.1', '5354', 'axfr-get', 'foo',
            os.path.join(self.backend._datafiles_dir, 'foo.zonedata'),
            os.path.join(self.backend._datafiles_dir, 'foo.ztmp')
        )

    def test_delete_zone_no_file(self):
        self.patch_ob(self.backend, '_rebuild_data_cdb')
        # Should not raise exceptions
        self.backend.delete_zone('non_existent_zone_file')

    @unittest.skipIf(not os.path.isfile(TINYDNSDATA_PATH),
                     "tinydns-data not installed")
    def test__rebuild_data_cdb_empty(self):
        # Check that tinydns-data can be run and the required files are
        # generated / renamed as needed
        self.CONF.set_override('root_helper', '  ')  # disable rootwrap
        self.backend._tinydns_cdb_filename = tempfile.mkstemp()[1]

        self.backend._rebuild_data_cdb()

        assert os.path.isfile(self.backend._tinydns_cdb_filename)
        os.remove(self.backend._tinydns_cdb_filename)

    @unittest.skipIf(not os.path.isfile(TINYDNSDATA_PATH),
                     "tinydns-data not installed")
    def test__rebuild_data_cdb(self):
        # Check that tinydns-data can be run and the required files are
        # generated / renamed as needed
        self.CONF.set_override('root_helper', '  ')  # disable rootwrap
        self.backend._tinydns_cdb_filename = tempfile.mkstemp()[1]

        fn = os.path.join(self.backend._datafiles_dir, 'example.org.zonedata')
        with open(fn, 'w') as f:
            f.write(""".example.org::ns1.example.org
+ns1.example.org:127.0.0.1
+www.example.org:127.0.0.1
""")

        self.backend._rebuild_data_cdb()

        assert os.path.isfile(self.backend._tinydns_cdb_filename)
        os.remove(self.backend._tinydns_cdb_filename)
