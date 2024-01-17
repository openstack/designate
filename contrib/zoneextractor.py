# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Artom Lifshitz <artom.lifshitz@enovance.com>
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

import argparse
import io
import logging
import os
import re
import sys

import dns.zone

logging.basicConfig()
LOG = logging.getLogger(__name__)


class Zone:
    """
    Encapsulates a dnspython zone to provide easier printing and writing to
    files
    """

    def __init__(self, dnszone):
        self._dnszone = dnszone

    def to_stdout(self):
        self.to_file(sys.stdout)

    def to_file(self, f):
        if isinstance(f, io.IOBase):
            fd = f
        elif type(f) is str:
            if os.path.isdir(f):
                fd = open(os.path.join(f, self._dnszone.origin.to_text()), 'w')
            else:
                fd = open(f, 'w')
        else:
            raise ValueError('f must be a file name or file object')
        fd.write('$ORIGIN %s\n' % self._dnszone.origin.to_text())
        self._dnszone.to_file(fd, relativize=False)
        fd.write('\n')
        if fd is not sys.stdout:
            fd.close()


class Extractor:
    """
    Extracts all the zones configured in a named.conf, including included
    files
    """

    # The regexes we use to extract information from the config file
    _include_regex = re.compile(
        r"""
        include \s*       # The include keyword, possibly followed by
                          # whitespace
        "                 # Open quote
        (?P<file> [^"]+ ) # The included file (without quotes), as group 'file'
        "                 # Close quote
        \s* ;             # Semicolon, possibly preceded by whitespace
        """, re.MULTILINE | re.VERBOSE)

    _zone_regex = re.compile(
        r"""
        zone \s*              # The zone keyword, possibly followed by
                              # whitespace
        "                     # Open quote
        (?P<name> [^"]+ )     # The zone name (without quotes), as group 'name'
        "                     # Close quote
        \s*                   # Possible whitespace
        {                     # Open bracket
        (?P<content> [^{}]+ ) # The contents of the zone block (without
                              # brackets) as group 'content'
        }                     # Close bracket
        \s* ;                 # Semicolon, possibly preceded by whitespace
        """, re.MULTILINE | re.VERBOSE)

    _type_master_regex = re.compile(
        r"""
        type \s+ # The type keyword, followed by some whitespace
        master   # The master keyword
        \s* ;    # Semicolon, possibly preceded by whitespace
        """, re.MULTILINE | re.VERBOSE)

    _zonefile_regex = re.compile(r"""
        file \s*          # The file keyword, possible followed by whitespace
        "                 # Open quote
        (?P<file> [^"]+ ) # The zonefile (without quotes), as group 'file'
        "                 # Close quote
        \s* ;             # Semicolor, possible preceded by whitespace
        """, re.MULTILINE | re.VERBOSE)

    def __init__(self, conf_file):
        self._conf_file = conf_file
        self._conf = self._filter_comments(conf_file)

    def _skip_until(self, f, stop):
        skip = ''
        while True:
            skip += f.read(1)
            if skip.endswith(stop):
                break

    def _filter_comments(self, conf_file):
        """
        Reads the named.conf, skipping comments and returning the filtered
        configuration
        """
        f = open(conf_file)
        conf = ''
        while True:
            c = f.read(1)
            if c == '':
                break
            conf += c
            # If we just appended a commenter:
            if conf.endswith('#'):
                self._skip_until(f, '\n')
                # Strip the '#' we appended earlier
                conf = conf[:-1]
            elif conf.endswith('//'):
                self._skip_until(f, '\n')
                # Strip the '//' we appended earlier
                conf = conf[:-2]
            elif conf.endswith('/*'):
                self._skip_until(f, '*/')
                # Strip the '/*' we appended earlier
                conf = conf[:-2]
        f.close()
        return conf

    def extract(self):
        zones = []
        zones.extend(self._process_includes())
        zones.extend(self._extract_zones())
        return zones

    def _process_includes(self):
        zones = []
        for include in self._include_regex.finditer(self._conf):
            x = Extractor(include.group('file'))
            zones.extend(x.extract())
        return zones

    def _extract_zones(self):
        zones = []
        for zone in self._zone_regex.finditer(self._conf):
            content = zone.group('content')
            name = zone.group('name')
            # Make sure it's a master zone:
            if self._type_master_regex.search(content):
                zonefile = self._zonefile_regex.search(content).group('file')
                try:
                    zone_object = dns.zone.from_file(zonefile,
                                                     allow_include=True)
                except dns.zone.UnknownOrigin:
                    LOG.info('%(zonefile)s is missing $ORIGIN, '
                             'inserting %(name)s',
                             {'zonefile': zonefile, 'name': name})
                    zone_object = dns.zone.from_file(zonefile,
                                                     allow_include=True,
                                                     origin=name)
                except dns.zone.NoSOA:
                    LOG.error('%s has no SOA', zonefile)
                zones.append(Zone(zone_object))
        return zones


def main():
    parser = argparse.ArgumentParser(
        description='Extract zonefiles from named.conf.')
    parser.add_argument('named_conf', metavar='FILE', type=str, nargs=1,
                        help='the named.conf to parse')
    parser.add_argument('-w', '--write', metavar='DIR', type=str,
                        help='Wwrite each extracted zonefile as its own file'
                        ' in DIR')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose output')
    args = parser.parse_args()
    if args.verbose:
        LOG.setLevel(logging.INFO)
    else:
        LOG.setLevel(logging.WARNING)
    try:
        x = Extractor(args.named_conf[0])
        for zone in x.extract():
            if args.write is not None:
                zone.to_file(args.write)
            else:
                zone.to_stdout()
    except OSError as e:
        LOG.error(e)


if __name__ == '__main__':
    sys.exit(main())
