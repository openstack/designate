# Copyright 2026 Cloudification GmbH
#
# Author: cloudification <contact@cloudification.io>
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

from designate.objects import base
from designate.objects import fields
from designate.objects.record import Record
from designate.objects.record import RecordList


@base.DesignateRegistry.register
class TLSA(Record):
    """
    TLSA record
    Defined in: RFC 6698
    """

    @staticmethod
    def validate_certificate_data(value):
        try:
            binascii.unhexlify(value)
        except Exception:
            raise ValueError("Certificate association data must be hex string")

    fields = {
        'usage': fields.IntegerFields(minimum=0, maximum=255),
        'selector': fields.IntegerFields(minimum=0, maximum=255),
        'matching_type': fields.IntegerFields(minimum=0, maximum=255),
        'certificate': fields.StringFields(maxLength=65535, nullable=False),
    }

    MATCHING_TYPE_LENGTHS = {
        1: 64,
        2: 128,
    }

    def from_string(self, value):
        value = value.replace("(", "").replace(")", "")
        values = value.split()

        if len(values) < 4:
            raise ValueError("TLSA record must have at least 4 fields")

        usage, selector, matching_type = values[:3]
        certificate = "".join(values[3:])

        if len(certificate) % 2 != 0:
            raise ValueError("Certificate hex data must have even length")
        try:
            matching_type_int = int(matching_type)
        except ValueError:
            raise ValueError("TLSA numeric fields must be integers")

        expected_len = TLSA.MATCHING_TYPE_LENGTHS.get(matching_type_int)
        if expected_len is not None and len(certificate) != expected_len:
            raise ValueError(
                "Certificate data for matching type %d must be exactly "
                "%d hex characters (%d bytes), got %d"
                % (matching_type_int, expected_len,
                   expected_len // 2, len(certificate))
            )

        TLSA.validate_certificate_data(certificate)
        try:
            self.usage = int(usage)
            self.selector = int(selector)
            self.matching_type = matching_type_int
        except ValueError:
            raise ValueError("TLSA numeric fields must be integers")
        self.certificate = certificate.lower()

    RECORD_TYPE = 52  # TLSA


@base.DesignateRegistry.register
class TLSAList(RecordList):

    LIST_ITEM_TYPE = TLSA

    fields = {
        'objects': fields.ListOfObjectsField('TLSA'),
    }
