# Copyright 2021 Cloudification GmbH
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

import base64

from designate.objects import base
from designate.objects import fields
from designate.objects.record import Record
from designate.objects.record import RecordList

VALID_ALGOS = [
    'RSAMD5', 'DSA', 'RSASHA1', 'DSA-NSEC3-SHA1', 'RSASHA1-NSEC3-SHA1',
    'RSASHA256', 'RSASHA512', 'ECC-GOST', 'ECDSAP256SHA256', 'ECDSAP384SHA384',
    'ED25519', 'ED448'
]
VALID_CERTS = [
    'PKIX', 'SPKI', 'PGP', 'IPKIX', 'ISPKI', 'IPGP', 'ACPKIX', 'IACPKIX',
    'URI', 'OID', 'DPKIX', 'DPTR'
]


@base.DesignateRegistry.register
class CERT(Record):
    """
    CERT Resource Record Type
    Defined in: RFC4398
    """
    fields = {
        'cert_type': fields.CertTypeField(),
        'key_tag': fields.IntegerFields(minimum=0, maximum=65535),
        'cert_algo': fields.CertAlgoField(),
        'certificate': fields.StringFields(),
    }

    @staticmethod
    def validate_cert_type(cert_type):
        if cert_type in VALID_CERTS:
            return cert_type

        try:
            int_cert_type = int(cert_type)
        except ValueError:
            raise ValueError('Cert type is not valid Mnemonic.')

        if int_cert_type < 0 or int_cert_type > 65535:
            raise ValueError(
                'Cert type value should be between 0 and 65535'
            )

        return cert_type

    @staticmethod
    def validate_cert_algo(cert_algo):
        if cert_algo in VALID_ALGOS:
            return cert_algo

        try:
            int_cert_algo = int(cert_algo)
        except ValueError:
            raise ValueError('Cert algorithm is not valid Mnemonic.')

        if int_cert_algo < 0 or int_cert_algo > 255:
            raise ValueError(
                'Cert algorithm value should be between 0 and 255'
            )

        return cert_algo

    @staticmethod
    def validate_cert_certificate(certificate):
        try:
            chunks = certificate.split(' ')
            encoded_chunks = []
            for chunk in chunks:
                encoded_chunks.append(chunk.encode())
            b64 = b''.join(encoded_chunks)
            base64.b64decode(b64)
        except Exception:
            raise ValueError('Cert certificate is not valid.')
        return certificate

    def from_string(self, value):
        cert_type, key_tag, cert_algo, certificate = value.split(' ', 3)

        self.cert_type = self.validate_cert_type(cert_type)
        self.key_tag = int(key_tag)
        self.cert_algo = self.validate_cert_algo(cert_algo)
        self.certificate = self.validate_cert_certificate(certificate)

    RECORD_TYPE = 37


@base.DesignateRegistry.register
class CERTList(RecordList):

    LIST_ITEM_TYPE = CERT

    fields = {
        'objects': fields.ListOfObjectsField('CERT'),
    }
