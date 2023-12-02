# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import dns.exception
import dns.message
import dns.opcode
import dns.rcode
import dns.rdatatype
import dns.renderer
import dns.tsig
from oslo_log import log as logging

import designate.conf
from designate import context
from designate import exceptions

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class DNSMiddleware:
    """Base DNS Middleware class with some utility methods"""
    def __init__(self, application):
        self.application = application

    def process_request(self, request):
        """Called on each request.

        If this returns None, the next application down the stack will be
        executed. If it returns a response then that response will be returned
        and execution will stop here.
        """
        return None

    def process_response(self, response):
        """Do whatever you'd like to the response."""
        return response

    def __call__(self, request):
        response = self.process_request(request)

        if response:
            return response

        response = self.application(request)
        return self.process_response(response)

    def _build_error_response(self):
        response = dns.message.make_response(
            dns.message.make_query('unknown', dns.rdatatype.A))
        response.set_rcode(dns.rcode.FORMERR)

        return response


class SerializationMiddleware(DNSMiddleware):
    """DNS Middleware to serialize/deserialize DNS Packets"""

    def __init__(self, application, tsig_keyring=None):
        super().__init__(application)
        self.tsig_keyring = tsig_keyring

    def __call__(self, request):
        # Generate the initial context. This may be updated by other middleware
        # as we learn more information about the Request.
        ctxt = context.DesignateContext.get_admin_context(all_tenants=True)

        message = None
        try:
            message = dns.message.from_wire(request['payload'],
                                            self.tsig_keyring)

            if message.had_tsig:
                LOG.debug('Request signed with TSIG key: %s', message.keyname)

            # Create + Attach the initial "environ" dict. This is similar to
            # the environ dict used in typical WSGI middleware.
            message.environ = {
                'context': ctxt,
                'addr': request['addr'],
            }
        except dns.message.UnknownTSIGKey:
            LOG.error(
                'Unknown TSIG key from %(host)s:%(port)d',
                {
                    'host': request['addr'][0],
                    'port': request['addr'][1]
                }
            )
        except dns.tsig.BadSignature:
            LOG.error(
                'Invalid TSIG signature from %(host)s:%(port)d',
                {
                    'host': request['addr'][0],
                    'port': request['addr'][1]
                }
            )
        except dns.exception.DNSException:
            LOG.error(
                'Failed to deserialize packet from %(host)s:%(port)d',
                {
                    'host': request['addr'][0],
                    'port': request['addr'][1]
                }
            )
        except Exception:
            LOG.exception(
                'Unknown exception deserializing packet '
                'from %(host)s %(port)d',
                {
                    'host': request['addr'][0],
                    'port': request['addr'][1]
                }
            )

        if message is None:
            # NOTE(eandersson): Unsure on the intent of the error handling
            #                   in this code. Cleaning the code path up, but
            #                   leaving functionality as it was.
            # error_response = self._build_error_response()
            # yield error_response.to_wire()
            yield
            return

        # Hand the Deserialized packet onto the Application
        for response in self.application(message):
            # Serialize and return the response if present
            if isinstance(response, dns.message.Message):
                yield response.to_wire(max_size=65535)
            elif isinstance(response, dns.renderer.Renderer):
                yield response.get_wire()
            else:
                LOG.error('Unexpected response %r', response)


class TsigInfoMiddleware(DNSMiddleware):
    """Middleware which looks up the information available for a TsigKey"""

    def __init__(self, application, storage):
        super().__init__(application)
        self.storage = storage

    def process_request(self, request):
        if not request.had_tsig:
            return None

        try:
            name = request.keyname.to_text(True)
            criterion = {'name': name}
            tsigkey = self.storage.find_tsigkey(
                context.get_current(), criterion
            )

            request.environ['tsigkey'] = tsigkey
            request.environ['context'].tsigkey_id = tsigkey.id

        except exceptions.TsigKeyNotFound:
            # This should never happen, as we just validated the key. Except
            # for race conditions.
            return self._build_error_response()

        return None
