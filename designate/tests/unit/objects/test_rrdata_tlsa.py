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

from designate import exceptions
from designate import objects

import oslotest.base

# Canonical test data for each matching type
# matching_type=0: full cert data, arbitrary even-length hex
TYPE0_HEX = 'aabbccddeeff'
# matching_type=1: SHA-256 → exactly 32 bytes = 64 hex chars
SHA256_HEX = 'ab' * 32
# matching_type=2: SHA-512 → exactly 64 bytes = 128 hex chars
SHA512_HEX = 'ab' * 64


class TLSATest(oslotest.base.BaseTestCase):

    def test_parse_tlsa(self):
        # Use matching_type=1 with correct SHA-256 length (64 hex chars)
        tlsa = objects.TLSA()
        tlsa.from_string('3 1 1 ' + SHA256_HEX)

        self.assertEqual(3, tlsa.usage)
        self.assertEqual(1, tlsa.selector)
        self.assertEqual(1, tlsa.matching_type)
        self.assertEqual(SHA256_HEX, tlsa.certificate)

    def test_multiline_and_parentheses(self):
        # Use matching_type=0 (no fixed length) to keep test focused
        # on multiline/parentheses parsing, not hash length
        tlsa = objects.TLSA()
        data = """3 1 0 (
            AA BB CC DD
            EE FF 00 11
        )"""
        tlsa.from_string(data)

        self.assertEqual(3, tlsa.usage)
        self.assertEqual(1, tlsa.selector)
        self.assertEqual(0, tlsa.matching_type)
        self.assertEqual('aabbccddeeff0011', tlsa.certificate)

    def test_spaces_in_certificate(self):
        # Use matching_type=0 to test space-stripping independently
        tlsa = objects.TLSA()
        tlsa.from_string('3 1 0 aa bb cc dd')
        self.assertEqual('aabbccdd', tlsa.certificate)

    def test_uppercase_normalization(self):
        # Use matching_type=0 to test lowercasing independently
        tlsa = objects.TLSA()
        tlsa.from_string('3 1 0 AABBCC')
        self.assertEqual('aabbcc', tlsa.certificate)

    def test_invalid_hex_data(self):
        # Use matching_type=0 so the invalid hex chars are caught
        # by validate_certificate_data, not the length check
        tlsa = objects.TLSA()
        with self.assertRaisesRegex(
                ValueError,
                "Certificate association data must be hex string"):
            tlsa.from_string('3 1 0 zzxxcc')

    def test_odd_length_hex(self):
        tlsa = objects.TLSA()
        with self.assertRaisesRegex(
                ValueError,
                "Certificate hex data must have even length"):
            tlsa.from_string('3 1 0 abc')

    def test_insufficient_fields(self):
        tlsa = objects.TLSA()
        with self.assertRaisesRegex(
                ValueError,
                "TLSA record must have at least 4 fields"):
            tlsa.from_string('3 1 1')

    def test_non_integer_fields(self):
        tlsa = objects.TLSA()
        with self.assertRaisesRegex(
                ValueError,
                "TLSA numeric fields must be integers"):
            tlsa.from_string('usage selector match aabbcc')

    def test_matching_type_1_correct_length(self):
        # SHA-256: exactly 64 hex chars must pass
        tlsa = objects.TLSA()
        tlsa.from_string('3 1 1 ' + SHA256_HEX)
        self.assertEqual(SHA256_HEX, tlsa.certificate)

    def test_matching_type_1_wrong_length(self):
        # SHA-256 with only 12 hex chars — must be rejected
        tlsa = objects.TLSA()
        with self.assertRaisesRegex(
                ValueError,
                "Certificate data for matching type 1 must be exactly "
                "64 hex characters"):
            tlsa.from_string('3 1 1 aabbccddeeff')

    def test_matching_type_2_correct_length(self):
        # SHA-512: exactly 128 hex chars must pass
        tlsa = objects.TLSA()
        tlsa.from_string('3 1 2 ' + SHA512_HEX)
        self.assertEqual(SHA512_HEX, tlsa.certificate)

    def test_matching_type_2_wrong_length(self):
        # SHA-512 with SHA-256-sized data — must be rejected
        tlsa = objects.TLSA()
        with self.assertRaisesRegex(
                ValueError,
                "Certificate data for matching type 2 must be exactly "
                "128 hex characters"):
            tlsa.from_string('3 1 2 ' + SHA256_HEX)

    def test_matching_type_0_arbitrary_length(self):
        # matching_type=0 (full data, no hash) — any even length is valid
        tlsa = objects.TLSA()
        tlsa.from_string('3 1 0 ' + TYPE0_HEX)
        self.assertEqual(TYPE0_HEX, tlsa.certificate)

    def test_recordset_validation(self):
        recordset = objects.RecordSet(
            name='_443._tcp.example.org.', type='TLSA',
            records=objects.RecordList(objects=[
                objects.Record(data='3 1 1 ' + SHA256_HEX)
            ])
        )
        recordset.validate()

    def test_recordset_invalid_data(self):
        recordset = objects.RecordSet(
            name='_443._tcp.example.org.', type='TLSA',
            records=objects.RecordList(objects=[
                objects.Record(data='3 1 0 invalid')
            ])
        )
        with self.assertRaises((exceptions.InvalidObject, ValueError)):
            recordset.validate()

    def test_empty_certificate_multiline(self):
        recordset = objects.RecordSet(
            name='_443._tcp.example.org.',
            type='TLSA',
            records=objects.RecordList(objects=[
                objects.Record(data='3 1 1 (   )'),
            ])
        )
        self.assertRaises(exceptions.InvalidObject, recordset.validate)

    def test_certificate_only_spaces(self):
        recordset = objects.RecordSet(
            name='_443._tcp.example.org.',
            type='TLSA',
            records=objects.RecordList(objects=[
                objects.Record(data='3 1 1    '),
            ])
        )
        self.assertRaises(exceptions.InvalidObject, recordset.validate)

    def test_empty_certificate(self):
        recordset = objects.RecordSet(
            name='_443._tcp.example.org.',
            type='TLSA',
            records=objects.RecordList(objects=[
                objects.Record(data='3 1 1 '),
            ])
        )
        self.assertRaises(exceptions.InvalidObject, recordset.validate)
