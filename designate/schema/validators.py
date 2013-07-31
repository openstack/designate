# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import datetime
import jsonschema
from designate.openstack.common import log as logging
from designate.schema import format


LOG = logging.getLogger(__name__)


class _Draft34CommonMixin(object):
    def validate_type(self, types, instance, schema):
        # NOTE(kiall): A datetime object is not a string, but is still valid.
        if ('format' in schema and schema['format'] == 'date-time'
                and isinstance(instance, datetime.datetime)):
            return

        errors = super(_Draft34CommonMixin, self).validate_type(
            types, instance, schema)

        for error in errors:
            yield error


class Draft4Validator(_Draft34CommonMixin, jsonschema.Draft4Validator):
    def __init__(self, schema, types=(), resolver=None, format_checker=None):
        if format_checker is None:
            format_checker = format.draft4_format_checker

        super(Draft4Validator, self).__init__(schema, types, resolver,
                                              format_checker)


class Draft3Validator(_Draft34CommonMixin, jsonschema.Draft3Validator):
    def __init__(self, schema, types=(), resolver=None, format_checker=None):
        if format_checker is None:
            format_checker = format.draft3_format_checker

        super(Draft3Validator, self).__init__(schema, types, resolver,
                                              format_checker)

    def validate_oneOf(self, oneOf, instance, schema):
        # Backported from Draft4 to Draft3
        subschemas = enumerate(oneOf)
        all_errors = []
        for index, subschema in subschemas:
            errors = list(self.descend(instance, subschema, schema_path=index))
            if not errors:
                first_valid = subschema
                break
            all_errors.extend(errors)
        else:
            yield jsonschema.ValidationError(
                "%r is not valid under any of the given schemas" % (instance,),
                context=all_errors,
            )

        more_valid = [s for i, s in subschemas if self.is_valid(instance, s)]
        if more_valid:
            more_valid.append(first_valid)
            reprs = ", ".join(repr(schema) for schema in more_valid)
            yield jsonschema.ValidationError(
                "%r is valid under each of %s" % (instance, reprs)
            )
