# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
from jsonschema import _utils


def type_draft3(validator, types, instance, schema):
    types = _utils.ensure_list(types)

    # NOTE(kiall): A datetime object is not a string, but is still valid.
    if ('format' in schema and schema['format'] == 'date-time'
            and isinstance(instance, datetime.datetime)):
        return

    all_errors = []
    for index, type in enumerate(types):
        if type == "any":
            return
        if validator.is_type(type, "object"):
            errors = list(validator.descend(instance, type, schema_path=index))
            if not errors:
                return
            all_errors.extend(errors)
        else:
            if validator.is_type(instance, type):
                return
    else:
        yield jsonschema.ValidationError(
            _utils.types_msg(instance, types), context=all_errors,
        )


def oneOf_draft3(validator, oneOf, instance, schema):
        # Backported from Draft4 to Draft3
        subschemas = iter(oneOf)
        first_valid = next(
            (s for s in subschemas if validator.is_valid(instance, s)), None,
        )

        if first_valid is None:
            yield jsonschema.ValidationError(
                "%r is not valid under any of the given schemas." % (instance,)
            )
        else:
            more_valid = [s for s in subschemas
                          if validator.is_valid(instance, s)]
            if more_valid:
                more_valid.append(first_valid)
                reprs = ", ".join(repr(schema) for schema in more_valid)
                yield jsonschema.ValidationError(
                    "%r is valid under each of %s" % (instance, reprs)
                )


def type_draft4(validator, types, instance, schema):
    types = _utils.ensure_list(types)

    # NOTE(kiall): A datetime object is not a string, but is still valid.
    if ('format' in schema and schema['format'] == 'date-time'
            and isinstance(instance, datetime.datetime)):
        return

    if not any(validator.is_type(instance, type) for type in types):
        yield jsonschema.ValidationError(_utils.types_msg(instance, types))
