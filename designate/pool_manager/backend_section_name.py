# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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

from oslo.config import iniparser

from designate import utils


GLOBAL_SECTION_NAME_LABEL = '*'
SECTION_NAME_PREFIX = 'backend'
SECTION_NAME_SEPARATOR = ':'
UUID_PATTERN = '-'.join([
    '[0-9A-Fa-f]{8}',
    '[0-9A-Fa-f]{4}',
    '[0-9A-Fa-f]{4}',
    '[0-9A-Fa-f]{4}',
    '[0-9A-Fa-f]{12}'

])
SECTION_PATTERN = SECTION_NAME_SEPARATOR.join([
    '^%s' % SECTION_NAME_PREFIX,
    '(.*)',
    '(%s)' % UUID_PATTERN
])
SECTION_LABELS = [
    'backend',
    'server_id'
]


class SectionNameParser(iniparser.BaseParser):
    """
    Used to retrieve the configuration file section names and parse the names.
    """

    def __init__(self, pattern, labels):
        super(SectionNameParser, self).__init__()
        self.regex = re.compile(pattern)
        self.labels = labels
        self.sections = []

    def assignment(self, key, value):
        pass

    def new_section(self, section):
        match = self.regex.match(section)
        if match:
            value = {
                'name': section
            }
            index = 1
            for label in self.labels:
                value[label] = match.group(index)
                index += 1
            self.sections.append(value)

    def parse(self, filename):
        with open(filename) as f:
            return super(SectionNameParser, self).parse(f)

    @classmethod
    def find_sections(cls, filename, pattern, labels):
        parser = cls(pattern, labels)
        parser.parse(filename)

        return parser.sections


def find_server_sections():
    """
    Find the server specific backend section names.

    A server specific backend section name is:

    [backend:<backend_driver>:<server_id>]
    """
    config_files = utils.find_config('designate.conf')

    all_sections = []
    for filename in config_files:
        sections = SectionNameParser.find_sections(
            filename, SECTION_PATTERN, SECTION_LABELS)
        all_sections.extend(sections)

    return all_sections


def _generate_section_name(backend_driver, label):
    """
    Generate the section name.

    A section name is:

    [backend:<backend_driver>:<label>]
    """
    return SECTION_NAME_SEPARATOR.join([
        SECTION_NAME_PREFIX,
        backend_driver,
        label
    ])


def generate_global_section_name(backend_driver):
    """
    Generate the global backend section name.

    A global backend section name is:

    [backend:<backend_driver>:*]
    """
    return _generate_section_name(backend_driver, GLOBAL_SECTION_NAME_LABEL)


def generate_server_section_name(backend_driver, server_id):
    """
    Generate the server specific backend section name.

    A server specific backend section name is:

    [backend:<backend_driver>:<server_id>]
    """
    return _generate_section_name(backend_driver, server_id)
