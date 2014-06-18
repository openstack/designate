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
import binascii

from mock import patch

from designate.tests.test_mdns import MdnsTestCase
from designate.mdns import handler


class MdnsRequestHandlerTest(MdnsTestCase):
    def setUp(self):
        super(MdnsRequestHandlerTest, self).setUp()
        self.handler = handler.RequestHandler()

    @patch.object(handler.RequestHandler, '_handle_query')
    def test_dispatch_opcode_query(self, mock):
        # DNS packet with QUERY opcode
        payload = ("abbe01200001000000000001076578616d706c6503636f6d0000010001"
                   "0000291000000000000000")

        self.handler.handle(binascii.a2b_hex(payload))
        self.assertTrue(mock.called)

    @patch.object(handler.RequestHandler, '_handle_unsupported')
    def test_dispatch_opcode_iquery(self, mock):
        # DNS packet with IQUERY opcode
        payload = "60e509000001000000000000076578616d706c6503636f6d0000010001"

        self.handler.handle(binascii.a2b_hex(payload))
        self.assertTrue(mock.called)

    @patch.object(handler.RequestHandler, '_handle_unsupported')
    def test_dispatch_opcode_status(self, mock):
        # DNS packet with STATUS opcode
        payload = "5e0811000001000000000000076578616d706c6503636f6d0000010001"

        self.handler.handle(binascii.a2b_hex(payload))
        self.assertTrue(mock.called)

    @patch.object(handler.RequestHandler, '_handle_unsupported')
    def test_dispatch_opcode_notify(self, mock):
        # DNS packet with NOTIFY opcode`
        payload = "93e121000001000000000000076578616d706c6503636f6d0000010001"

        self.handler.handle(binascii.a2b_hex(payload))
        self.assertTrue(mock.called)

    @patch.object(handler.RequestHandler, '_handle_unsupported')
    def test_dispatch_opcode_update(self, mock):
        # DNS packet with UPDATE opcode`
        payload = "5a7029000001000000000000076578616d706c6503636f6d0000010001"

        self.handler.handle(binascii.a2b_hex(payload))
        self.assertTrue(mock.called)
