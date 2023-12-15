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


from unittest import mock

import dns
import dns.query
import dns.tsigkeyring

import designate.conf
from designate import dnsmiddleware
from designate import dnsutils
from designate.mdns import handler
from designate import storage
import designate.tests.functional


CONF = designate.conf.CONF


class TestSerializationMiddleware(designate.tests.functional.TestCase):
    def setUp(self):
        super().setUp()
        self.storage = storage.get_storage()
        self.tg = mock.Mock()

    def test_with_tsigkeyring(self):
        self.create_tsigkey(fixture=1)

        query = dns.message.make_query(
            'example.com.', dns.rdatatype.SOA,
        )
        query.use_tsig(dns.tsigkeyring.from_text(
            {'test-key-two': 'AnotherSecretKey'})
        )
        payload = query.to_wire()

        application = handler.RequestHandler(self.storage, self.tg)
        application = dnsmiddleware.SerializationMiddleware(
            application, dnsutils.TsigKeyring(self.storage)
        )

        self.assertTrue(next(application(
            {'payload': payload, 'addr': ['192.0.2.1', 5353]}
        )))

    def test_without_tsigkeyring(self):
        query = dns.message.make_query(
            'example.com.', dns.rdatatype.SOA,
        )
        payload = query.to_wire()

        application = handler.RequestHandler(self.storage, self.tg)
        application = dnsmiddleware.SerializationMiddleware(
            application, dnsutils.TsigKeyring(self.storage)
        )

        self.assertTrue(next(application(
            {'payload': payload, 'addr': ['192.0.2.1', 5353]}
        )))
