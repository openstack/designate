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
import testtools
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

        with testtools.ExpectedException(exceptions.ResourceNotFound):
            utils.resource_string(name)

    def test_load_schema(self):
        schema = utils.load_schema('v1', 'domain')

        self.assertIsInstance(schema, dict)

    def test_load_schema_missing(self):
        with testtools.ExpectedException(exceptions.ResourceNotFound):
            utils.load_schema('v1', 'missing')

    def test_load_template(self):
        name = 'bind9-config.jinja2'

        template = utils.load_template(name)

        self.assertIsInstance(template, Template)

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
