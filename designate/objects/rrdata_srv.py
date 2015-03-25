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
from designate.objects.record import Record


class RRData_SRV(Record):
    """
    SRV Resource Record Type
    Defined in: RFC2782
    """
    FIELDS = {
        'priority': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 65535
            },
            'required': True
        },
        'weight': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 65535
            },
            'required': True
        },
        'port': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 65535
            },
            'required': True
        },
        'target': {
            'schema': {
                'type': 'string',
                'format': 'domainname',
                'maxLength': 255,
            },
            'required': True
        }
    }

    def _to_string(self):
        return "%(priority)s %(weight)s %(target)s %(port)s" % self

    def _from_string(self, value):
        self.priortiy, self.weight, self.port, self.target = value.split(' ')

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 33
