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
from jsonschema import validators

from designate.schema import _validators


Draft3Validator = validators.extend(
    validators.Draft3Validator,
    validators={
        "type": _validators.type_draft3,
        "oneOf": _validators.oneOf_draft3,
    })

Draft4Validator = validators.extend(
    validators.Draft4Validator,
    validators={
        "type": _validators.type_draft4,
    })
