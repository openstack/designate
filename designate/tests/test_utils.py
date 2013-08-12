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
from jinja2 import Template
from designate.tests import TestCase
from designate import exceptions
from designate import utils


class TestUtils(TestCase):
    def test_resource_string(self):
        name = ['templates', 'bind9-config.jinja2']

        resource_string = utils.resource_string(*name)

        self.assertIsNotNone(resource_string)

    def test_resource_string_missing(self):
        name = 'invalid.jinja2'

        with self.assertRaises(exceptions.ResourceNotFound):
            utils.resource_string(name)

    def test_load_schema(self):
        schema = utils.load_schema('v1', 'domain')

        self.assertIsInstance(schema, dict)

    def test_load_schema_missing(self):
        with self.assertRaises(exceptions.ResourceNotFound):
            utils.load_schema('v1', 'missing')

    def test_load_template(self):
        name = 'bind9-config.jinja2'

        template = utils.load_template(name)

        self.assertIsInstance(template, Template)

    def test_load_template_missing(self):
        name = 'invalid.jinja2'

        with self.assertRaises(exceptions.ResourceNotFound):
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

    def test_quote_string(self):
        self.assertEqual('""', utils.quote_string(''))
        self.assertEqual('""', utils.quote_string('"'))
        self.assertEqual('""', utils.quote_string('""'))
        self.assertEqual('"hello"', utils.quote_string('hello'))
        self.assertEqual('"hello1" "hello2"',
                         utils.quote_string('hello1 hello2'))
        self.assertEqual('"hello1" "hello2"',
                         utils.quote_string('"hello1" hello2'))
        self.assertEqual('"hello1" "hello2"',
                         utils.quote_string('hello1 "hello2"'))
        self.assertEqual('"hello1" "hello2" "hello3"',
                         utils.quote_string('"hello1" hello2 "hello3"'))
        self.assertEqual('"properly quoted string"',
                         utils.quote_string('"properly quoted string"'))
        self.assertEqual('"not" "properly" "quoted" "string"',
                         utils.quote_string('not properly quoted string'))
        self.assertEqual('"properly quoted \\" string"',
                         utils.quote_string('"properly quoted \\" string"'))
        self.assertEqual('"single" "quote" "at" "the" "end\\""',
                         utils.quote_string('single quote at the end"'))
        self.assertEqual('"single" "quote" "in\\"" "the" "middle"',
                         utils.quote_string('single quote in\\" the middle'))
        self.assertEqual('"single quote at the start"',
                         utils.quote_string('"single quote at the start'))
