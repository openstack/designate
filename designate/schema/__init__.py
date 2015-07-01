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
from oslo_log import log as logging

from designate import exceptions
from designate import utils
from designate.schema import validators
from designate.schema import resolvers
from designate.schema import format

LOG = logging.getLogger(__name__)


class Schema(object):
    def __init__(self, version, name):
        self.raw_schema = utils.load_schema(version, name)
        self.resolver = resolvers.LocalResolver.from_schema(
            version, self.raw_schema)

        if version == 'v1':
            self.validator = validators.Draft3Validator(
                self.raw_schema, resolver=self.resolver,
                format_checker=format.draft3_format_checker)
        elif version in ['v2', 'admin']:
            self.validator = validators.Draft4Validator(
                self.raw_schema, resolver=self.resolver,
                format_checker=format.draft4_format_checker)
        else:
            raise Exception('Unknown API version: %s' % version)

    @property
    def schema(self):
        return self.validator.schema

    @property
    def properties(self):
        return self.schema['properties']

    @property
    def links(self):
        return self.schema['links']

    @property
    def raw(self):
        return self.raw_schema

    def validate(self, obj):
        LOG.debug('Validating values: %r' % obj)
        errors = []

        for error in self.validator.iter_errors(obj):
            errors.append({
                'path': ".".join([str(x) for x in error.path]),
                'message': error.message,
                'validator': error.validator
            })

        if len(errors) > 0:
            LOG.debug('Errors in validation: %r' % errors)
            raise exceptions.InvalidObject("Provided object does not match "
                                           "schema", errors=errors)

    def filter(self, instance, properties=None):
        if not properties:
            properties = self.properties

        filtered = {}

        for name, subschema in list(properties.items()):
            if 'type' in subschema and subschema['type'] == 'array':
                subinstance = instance.get(name, None)
                filtered[name] = self._filter_array(subinstance, subschema)
            elif 'type' in subschema and subschema['type'] == 'object':
                subinstance = instance.get(name, None)
                properties = subschema['properties']
                filtered[name] = self.filter(subinstance, properties)
            else:
                filtered[name] = instance.get(name, None)

        return filtered

    def _filter_array(self, instance, schema):
        if 'items' in schema and isinstance(schema['items'], list):
            # NOTE(kiall): We currently don't make use of this..
            raise NotImplementedError()

        elif 'items' in schema:
            schema = schema['items']

            if '$ref' in schema:
                with self.resolver.resolving(schema['$ref']) as ischema:
                    schema = ischema

            properties = schema['properties']

            return [self.filter(i, properties) for i in instance]

        elif 'properties' in schema:
            schema = schema['properties']

            with self.resolver.resolving(schema['$ref']) as ischema:
                    schema = ischema

            return [self.filter(i, schema) for i in instance]

        else:
            raise NotImplementedError('Can\'t filter unknown array type')
