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


class RRData_SSHFP(Record):
    """
    SSHFP Resource Record Type
    Defined in: RFC4255
    """
    FIELDS = {
        'algorithm': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 2
            },
            'required': True
        },
        'fp_type': {
            'schema': {
                'type': 'integer',
                'minimum': 0,
                'maximum': 1
            },
            'required': True
        },
        'fingerprint': {
            'schema': {
                'type': 'string',
                'format': 'sshfp'
            },
            'required': True
        }
    }

    def _to_string(self):
        return "%(algorithm)s %(fp_type)s %(fingerprint)s" % self

    def _from_string(self, value):
        self.algorithm, self.fp_type, self.fingerprint = value.split(' ')

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 44
