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

from designate.exceptions import InvalidObject
from designate.objects import base
from designate.objects import fields
from designate.objects.record import Record
from designate.objects.record import RecordList


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

    def validate_cert_type(self, cert_type):
        try:
            int_cert_type = int(cert_type)
            if int_cert_type < 0 or int_cert_type > 65535:
                err = ("Cert type value should be between 0 and 65535")
                raise InvalidObject(err)
        except ValueError:
            # cert type is specified as Mnemonic
            VALID_CERTS = ['PKIX', 'SPKI', 'PGP', 'IPKIX', 'ISPKI', 'IPGP',
                           'ACPKIX', 'IACPKIX', 'URI', 'OID', 'DPKIX', 'DPTR']
            if cert_type not in VALID_CERTS:
                err = ("Cert type is not valid Mnemonic.")
                raise InvalidObject(err)
        return cert_type

    def validate_cert_algo(self, cert_algo):
        try:
            int_cert_algo = int(cert_algo)
            if int_cert_algo < 0 or int_cert_algo > 255:
                err = ("Cert algorithm value should be between 0 and 255")
                raise InvalidObject(err)
        except ValueError:
            # cert algo is specified as Mnemonic
            VALID_ALGOS = ['RSAMD5', 'DSA', 'RSASHA1', 'DSA-NSEC3-SHA1',
                           'RSASHA1-NSEC3-SHA1', 'RSASHA256', 'RSASHA512',
                           'ECC-GOST', 'ECDSAP256SHA256', 'ECDSAP384SHA384',
                           'ED25519', 'ED448']
            if cert_algo not in VALID_ALGOS:
                err = ("Cert algorithm is not valid Mnemonic.")
                raise InvalidObject(err)
        return cert_algo

    def validate_cert_certificate(self, certificate):
        try:
            chunks = certificate.split(' ')
            encoded_chunks = []
            for chunk in chunks:
                encoded_chunks.append(chunk.encode())
            b64 = b''.join(encoded_chunks)
            base64.b64decode(b64)
        except Exception:
            err = ("Cert certificate is not valid.")
            raise InvalidObject(err)
        return certificate

    def _to_string(self):
        return ("%(cert_type)s %(key_tag)s %(cert_algo)s "
                "%(certificate)s" % self)

    def _from_string(self, v):
        cert_type, key_tag, cert_algo, certificate = v.split(' ', 3)

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
