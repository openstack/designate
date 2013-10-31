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
import jsonschema
from designate.openstack.common import log as logging
from designate.schema import _validators


LOG = logging.getLogger(__name__)


# JSONSchema 1.3 to 2.0 compatibility
try:
    # JSONSchema 2+
    from jsonschema import _utils  # flake8: noqa
    from jsonschema import validators
    JS2 = True
    Draft3ValidatorBase = validators.Draft3Validator
    Draft4ValidatorBase = validators.Draft4Validator
except ImportError:
    # JSONSchema 1.3
    JS2 = False
    Draft3ValidatorBase = jsonschema.Draft3Validator
    Draft4ValidatorBase = jsonschema.Draft4Validator


if JS2:
    Draft3Validator = validators.extend(
        Draft3ValidatorBase,
        validators={
            "type": _validators.type_draft3,
            "oneOf": _validators.oneOf_draft3,
        })

    Draft4Validator = validators.extend(
        Draft4ValidatorBase,
        validators={
            "type": _validators.type_draft4,
        })

else:
    class Draft3Validator(Draft3ValidatorBase):
        def validate_type(self, types, instance, schema):
            for i in _validators.type_draft3(self, types, instance,
                                             schema):
                yield i

        def validate_oneOf(self, oneOf, instance, schema):
            for i in _validators.oneOf_draft3(self, oneOf, instance, schema):
                yield i

    class Draft4Validator(Draft4ValidatorBase):
        def validate_type(self, types, instance, schema):
            for i in _validators.type_draft4(self, types, instance,
                                             schema):
                yield i
