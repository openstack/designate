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

import os
import tempfile
import unittest

import testtools
from jinja2 import Template

from designate.tests import TestCase
from designate import exceptions
from designate import utils


class TestUtils(TestCase):
    def test_resource_string(self):
        name = ['templates', 'bind9-zone.jinja2']

        resource_string = utils.resource_string(*name)

        self.assertIsNotNone(resource_string)

    def test_resource_string_missing(self):
        name = 'invalid.jinja2'

        with testtools.ExpectedException(exceptions.ResourceNotFound):
            utils.resource_string(name)

    def test_resource_string_empty_args(self):
        with testtools.ExpectedException(ValueError):
            utils.resource_string()

    def test_load_schema(self):
        schema = utils.load_schema('v1', 'domain')

        self.assertIsInstance(schema, dict)

    def test_load_schema_missing(self):
        with testtools.ExpectedException(exceptions.ResourceNotFound):
            utils.load_schema('v1', 'missing')

    def test_load_template(self):
        name = 'bind9-zone.jinja2'

        template = utils.load_template(name)

        self.assertIsInstance(template, Template)

    def test_load_template_keep_trailing_newline(self):
        name = 'bind9-zone.jinja2'
        template = utils.load_template(name)
        self.assertTrue(template.environment.keep_trailing_newline)

    def test_load_template_missing(self):
        name = 'invalid.jinja2'

        with testtools.ExpectedException(exceptions.ResourceNotFound):
            utils.load_template(name)

    def test_render_template(self):
        template = Template("Hello {{name}}")

        result = utils.render_template(template, name="World")

        self.assertEqual('Hello World', result)

    def test_render_template_to_file(self):
        output_path = tempfile.mktemp()

        template = Template("Hello {{name}}")

        utils.render_template_to_file(template, output_path=output_path,
                                      name="World")

        self.assertTrue(os.path.exists(output_path))

        try:
            with open(output_path, 'r') as fh:
                self.assertEqual('Hello World', fh.read())
        finally:
            os.unlink(output_path)

    def test_increment_serial(self):
        ret_serial = utils.increment_serial(serial=20)
        self.assertGreater(ret_serial, 20)

    def test_is_uuid_like(self):
        uuid_str = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        self.assertTrue(utils.is_uuid_like(uuid_str))
        uuid_str = '678'
        self.assertFalse(utils.is_uuid_like(uuid_str))

    def test_split_host_port(self):
        host_port = "abc:abc"
        host, port = utils.split_host_port(host_port)
        self.assertEqual((host, port), ("abc:abc", 53))

        host_port = "abc:25"
        host, port = utils.split_host_port(host_port)
        self.assertEqual((host, port), ("abc", 25))

    def test_get_paging_params_invalid_limit(self):
        for value in [9223372036854775809, -1]:
            with testtools.ExpectedException(exceptions.InvalidLimit):
                utils.get_paging_params({'limit': value}, [])

    def test_get_paging_params_max_limit(self):
        self.config(max_limit_v2=1000, group='service:api')
        result = utils.get_paging_params({'limit': "max"}, [])
        self.assertEqual(result[1], 1000)

    def test_get_paging_params_invalid_sort_dir(self):
        with testtools.ExpectedException(exceptions.InvalidSortDir):
            utils.get_paging_params({'sort_dir': "dsc"}, [])

    def test_get_paging_params_invalid_sort_key(self):
        with testtools.ExpectedException(exceptions.InvalidSortKey):
            utils.get_paging_params({'sort_key': "dsc"}, ['asc', 'desc'])


class SocketListenTest(unittest.TestCase):

    def test_listen_tcp(self):
        # Test listening on TCP on IPv4 and IPv6 addrs
        # bug 1566036
        for addr in ('', '0.0.0.0', '127.0.0.1', '::', '::1'):
            s = utils.bind_tcp(addr, 0, 1)
            s.close()

    def test_listen_udp(self):
        # Test listening on UDP on IPv4 and IPv6 addrs
        for addr in ('', '0.0.0.0', '127.0.0.1', '::', '::1'):
            s = utils.bind_udp(addr, 0)
            s.close()
