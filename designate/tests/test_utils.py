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
import functools
import tempfile
import unittest

import six
import testtools
from mock import Mock
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
        context = Mock()
        for value in [9223372036854775809, -1]:
            with testtools.ExpectedException(exceptions.InvalidLimit):
                utils.get_paging_params(context, {'limit': value}, [])

    def test_get_paging_params_max_limit(self):
        context = Mock()
        self.config(max_limit_v2=1000, group='service:api')
        result = utils.get_paging_params(context, {'limit': "max"}, [])
        self.assertEqual(result[1], 1000)

    def test_get_paging_params_invalid_sort_dir(self):
        context = Mock()
        with testtools.ExpectedException(exceptions.InvalidSortDir):
            utils.get_paging_params(context, {'sort_dir': "dsc"}, [])

    def test_get_paging_params_invalid_sort_key(self):
        context = Mock()
        with testtools.ExpectedException(exceptions.InvalidSortKey):
            utils.get_paging_params(context, {'sort_key': "dsc"},
                                    ['asc', 'desc'])


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


def def_method(f, *args, **kwargs):
    @functools.wraps(f)
    def new_method(self):
        return f(self, *args, **kwargs)
    return new_method


def parameterized_class(cls):
    """A class decorator for running parameterized test cases.
    Mark your class with @parameterized_class.
    Mark your test cases with @parameterized.
    """
    test_functions = {
        k: v for k, v in vars(cls).items() if k.startswith('test')
    }
    for name, f in test_functions.items():
        if not hasattr(f, '_test_data'):
            continue

        # remove the original test function from the class
        delattr(cls, name)

        # add a new test function to the class for each entry in f._test_data
        for tag, args in f._test_data.items():
            new_name = "{0}_{1}".format(f.__name__, tag)
            if hasattr(cls, new_name):
                raise Exception(
                    "Parameterized test case '{0}.{1}' created from '{0}.{2}' "
                    "already exists".format(cls.__name__, new_name, name))

            # Using `def new_method(self): f(self, **args)` is not sufficient
            # (all new_methods use the same args value due to late binding).
            # Instead, use this factory function.
            new_method = def_method(f, **args)

            # To add a method to a class, available for all instances:
            #   MyClass.method = types.MethodType(f, None, MyClass)
            setattr(cls, new_name, six.create_unbound_method(new_method, cls))
    return cls


def parameterized(data):
    """A function decorator for parameterized test cases.
    Example:
        @parameterized({
            'zero': dict(val=0),
            'one': dict(val=1),
        })
        def test_val(self, val):
            self.assertEqual(self.get_val(), val)
    The above will generate two test cases:
        `test_val_zero` which runs with val=0
        `test_val_one` which runs with val=1
    :param data: A dictionary that looks like {tag: {arg1: val1, ...}}
    """
    def wrapped(f):
        f._test_data = data
        return f
    return wrapped
