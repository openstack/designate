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
import dns
from oslo.config import cfg

from designate.openstack.common import log as logging
from designate import storage


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class RequestHandler(object):
    def __init__(self):
        # Get a storage connection
        storage_driver = cfg.CONF['service:mdns'].storage_driver
        self.storage = storage.get_storage(storage_driver)

    def handle(self, payload):
        request = dns.message.from_wire(payload)

        # As we move further with the implementation, we'll want to:
        # 1) Decode the payload using DNSPython
        # 2) Hand off to either _handle_query or _handle_unsupported
        #    based on the OpCode
        # 3) Gather the query results from storage
        # 4) Build and return response using DNSPython.

        if request.opcode() == dns.opcode.QUERY:
            response = self._handle_query(request)
        else:
            response = self._handle_unsupported(request)

        return response.to_wire()

    def _handle_query(self, request):
        """ Handle a DNS QUERY request """
        response = dns.message.make_response(request)
        response.set_rcode(dns.rcode.SERVFAIL)

        return response

    def _handle_unsupported(self, request):
        """
        Handle Unsupported DNS OpCode's

        Unsupported OpCode's include STATUS, IQUERY, NOTIFY, UPDATE
        """
        response = dns.message.make_response(request)
        response.set_rcode(dns.rcode.REFUSED)

        return response
