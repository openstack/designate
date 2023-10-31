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
import jsonschema
from oslo_log import log as logging

from designate import exceptions
from designate import utils

LOG = logging.getLogger(__name__)


class Schema:
    def __init__(self, version, name):
        self.raw_schema = utils.load_schema(version, name)
        self.validator = jsonschema.Draft4Validator(self.raw_schema)

    def validate(self, obj):
        LOG.debug('Validating values: %r', obj)
        errors = []

        for error in self.validator.iter_errors(obj):
            errors.append({
                'path': '.'.join([str(x) for x in error.path]),
                'message': error.message,
                'validator': error.validator
            })

        if errors:
            LOG.debug('Errors in validation: %r', errors)
            raise exceptions.InvalidObject(
                'Provided object does not match schema',
                errors=errors
            )
