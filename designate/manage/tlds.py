# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import csv
import os

from oslo_log import log as logging

from designate.central import rpcapi as central_rpcapi
from designate.common import constants
import designate.conf
from designate import exceptions
from designate.manage import base
from designate import objects
from designate import rpc


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class TLDCommands(base.Commands):
    """
    Import TLDs to Designate.  The format of the command is:
    designate-manage tlds import --input_file="<complete path to input file>"
    [--delimiter="delimiter character"]
    The TLDs need to be provided in a csv file.  Each line in
    this file contains a TLD entry followed by an optional description.
    By default the delimiter character is ","

    If any lines in the input file result in an error, the program
    continues to the next line.

    On completion the output is reported (LOG.info) in the format:
    Number of tlds added: <number>

    If there are any errors, they are reported (LOG.err) in the format:
    <Error> --> <Line causing the error>

    <Error> can be one of the following:
    DuplicateTld - This occurs if the TLD is already present.
    InvalidTld - This occurs if the TLD does not conform to the TLD schema.
    InvalidDescription - This occurs if the description does not conform to
        the description schema
    InvalidLine - This occurs if the line contains more than 2 fields.
    """

    def __init__(self):
        super().__init__()

    def _startup(self):
        rpc.init(CONF)
        self.central_api = central_rpcapi.CentralAPI()

    # The dictionary function __str__() does not list the fields in any
    # particular order.
    # It makes it easier to read if the tld_name is printed first, so we have
    # a separate function to do the necessary conversions
    def _convert_tld_dict_to_str(self, line):
        keys = ['name', 'description', 'extra_fields']
        values = [line['name'],
                  line['description'],
                  line['extra_fields'] if 'extra_fields' in line else None]
        dict_str = ''.join([str.format("'{0}': '{1}', ", keys[x], values[x])
                            for x in range(len(values)) if values[x]])

        return '{' + dict_str.rstrip(' ,') + '}'

    # validates and returns the number of tlds added - either 0 in case of
    # any errors or 1 if everything is successful
    # In case of errors, the error message is appended to the list error_lines
    def _validate_and_create_tld(self, line, error_lines):
        # validate the tld name
        if not constants.RE_TLDNAME.match(line['name']):
            error_lines.append('InvalidTld --> ' +
                               self._convert_tld_dict_to_str(line))
            return 0
        # validate the description if there is one
        elif (line['description']) and (len(line['description']) > 160):
            error_lines.append('InvalidDescription --> ' +
                               self._convert_tld_dict_to_str(line))

            return 0
        else:
            try:
                self.central_api.create_tld(self.context,
                                            tld=objects.Tld.from_dict(line))
                return 1
            except exceptions.DuplicateTld:
                error_lines.append('DuplicateTld --> ' +
                                   self._convert_tld_dict_to_str(line))
                return 0

    @base.name('import')
    @base.args('--input_file', help='Input file path containing TLDs',
               required=True, type=str)
    @base.args('--delimiter',
               help='delimiter between fields in the input file',
               default=',', type=str)
    def from_file(self, input_file=None, delimiter=None):
        self._startup()

        if not os.path.exists(input_file):
            raise Exception('TLD Input file Not Found')

        LOG.info('Importing TLDs from %s', input_file)

        error_lines = []
        tlds_added = 0

        with open(input_file) as inf:
            csv.register_dialect('import-tlds', delimiter=delimiter)
            reader = csv.DictReader(inf,
                                    fieldnames=['name', 'description'],
                                    restkey='extra_fields',
                                    dialect='import-tlds')
            for line in reader:
                # check if there are more than 2 fields
                if 'extra_fields' in line:
                    error_lines.append('InvalidLine --> ' +
                                       self._convert_tld_dict_to_str(line))
                else:
                    tlds_added += self._validate_and_create_tld(line,
                                                                error_lines)

        LOG.info('Number of tlds added: %d', tlds_added)

        if error_lines:
            LOG.error('Number of errors: %d', len(error_lines))
            # Sorting the errors and printing them so that it is easier to
            # read the errors
            LOG.error('Error Lines:\n%s', '\n'.join(sorted(error_lines)))
