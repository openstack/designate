#!/usr/bin/env python
# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

"""
A simple mock UDP server to receive monasca-statsd traffic
Log to stdout or to a file.
"""

from argparse import ArgumentParser
import sys
from time import gmtime
from time import strftime
import SocketServer


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('--addr', default='127.0.0.1',
                    help='Listen IP addr (default: 127.0.0.1)')
    ap.add_argument('--port', default=8125, type=int,
                    help='UDP port (default: 8125)')
    ap.add_argument('--output-fname', default=None,
                    help='Output file (default: stdout)')
    return ap.parse_args()


class StatsdMessageHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        tstamp = strftime("%Y-%m-%dT%H:%M:%S", gmtime())
        if self._output_fd:
            self._output_fd.write("%s %s\n" % (tstamp, data))
        else:
            print("%s %s" % (tstamp, data))


def main():
    args = parse_args()
    fd = open(args.output_fname, 'a') if args.output_fname else None
    StatsdMessageHandler._output_fd = fd
    server = SocketServer.UDPServer(
        (args.addr, args.port),
        StatsdMessageHandler,
    )
    server.serve_forever()

if __name__ == "__main__":
    sys.exit(main())
