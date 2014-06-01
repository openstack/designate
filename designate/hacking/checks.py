# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import re


mutable_default_argument_check = re.compile(
    r"def [a-zA-Z0-9].*\(.*(\{|\[|\().*\)\:")


def mutable_default_arguments(logical_line, filename):
    if mutable_default_argument_check.match(logical_line):
        yield (0, "D701: Default paramater value is a mutable type")


def factory(register):
    register(mutable_default_arguments)
