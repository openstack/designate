# Copyright 2015 Hewlett-Packard Development Company, L.P.
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
from __future__ import print_function

import re
import sys
import linecache

from prettytable import PrettyTable

PEP8_LINE = r'^((?P<file>.*):(?P<line>\d*):(?P<col>\d*):) ' \
            '(?P<error>(?P<error_code>\w\d{1,3})(?P<error_desc>.*$))'

HTML = True


def main():

    raw_errors = []

    max_filename_len = 0
    for line in sys.stdin:
        m = re.match(PEP8_LINE, line)
        if m:
            m = m.groupdict()
            raw_errors.append(m)
            if len(m['file']) > max_filename_len:
                max_filename_len = len(m['file'])
        else:
            print(line)

    if len(raw_errors) > 0:

        print('Flake8 Results')

        ct = PrettyTable([
            "File",
            "Line",
            "Column",
            "Error Code",
            "Error Message",
            "Code"
        ])

        ct.align["File"] = "l"
        ct.align["Error Message"] = "l"
        ct.align["Code"] = "l"

        for line in raw_errors:
            ct.add_row(format_dict(line))

        print(ct)

        with open('flake8_results.html', 'w') as f:
            f.write('<html><head><style type="text/css">table a:link{color:#666;font-weight:700;text-decoration:none}table a:visited{color:#999;font-weight:700;text-decoration:none}table a:active,table a:hover{color:#bd5a35;text-decoration:underline}table{font-family:Arial,Helvetica,sans-serif;color:#666;font-size:12px;text-shadow:1px 1px 0 #fff;background:#eaebec;margin:20px;border:1px solid #ccc;-moz-border-radius:3px;-webkit-border-radius:3px;border-radius:3px;-moz-box-shadow:0 1px 2px #d1d1d1;-webkit-box-shadow:0 1px 2px #d1d1d1;box-shadow:0 1px 2px #d1d1d1}table th{padding:21px 25px 22px;border-top:1px solid #fafafa;border-bottom:1px solid #e0e0e0;background:#ededed;background:-webkit-gradient(linear,left top,left bottom,from(#ededed),to(#ebebeb));background:-moz-linear-gradient(top,#ededed,#ebebeb)}table th:first-child{text-align:left;padding-left:20px}table tr:first-child th:first-child{-moz-border-radius-topleft:3px;-webkit-border-top-left-radius:3px;border-top-left-radius:3px}table tr:first-child th:last-child{-moz-border-radius-topright:3px;-webkit-border-top-right-radius:3px;border-top-right-radius:3px}table tr{text-align:left;padding-left:20px}table td:first-child{text-align:left;padding-left:20px;border-left:0}table td{padding:18px;border-top:1px solid #fff;border-bottom:1px solid #e0e0e0;border-left:1px solid #e0e0e0;background:#fafafa;background:-webkit-gradient(linear,left top,left bottom,from(#fbfbfb),to(#fafafa));background:-moz-linear-gradient(top,#fbfbfb,#fafafa)}table tr.even td{background:#f6f6f6;background:-webkit-gradient(linear,left top,left bottom,from(#f8f8f8),to(#f6f6f6));background:-moz-linear-gradient(top,#f8f8f8,#f6f6f6)}table tr:last-child td{border-bottom:0}table tr:last-child td:first-child{-moz-border-radius-bottomleft:3px;-webkit-border-bottom-left-radius:3px;border-bottom-left-radius:3px}table tr:last-child td:last-child{-moz-border-radius-bottomright:3px;-webkit-border-bottom-right-radius:3px;border-bottom-right-radius:3px}table tr:hover td{background:#f2f2f2;background:-webkit-gradient(linear,left top,left bottom,from(#f2f2f2),to(#f0f0f0));background:-moz-linear-gradient(top,#f2f2f2,#f0f0f0)}</style></head><body>%s</body</html>' % ct.get_html_string(attributes = {"cellspacing": 0})) # noqa


def format_dict(raw):
    output = []
    if raw['file'].startswith('./'):
        output.append(raw['file'][2:])
    else:
        output.append(raw['file'])

    output.append(raw['line'])
    output.append(raw['col'])
    output.append(raw['error_code'])

    output.append(raw['error_desc'].lstrip())

    code_string = linecache.getline(
        output[0],
        int(raw['line'])).lstrip().rstrip()

    output.append(code_string)

    return output

if __name__ == '__main__':
    sys.exit(main())
