# Copyright 2026 Red Hat, Inc.
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
import os
import tempfile
from unittest import mock

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from oslo_utils import timeutils
import oslotest.base

from designate.common import crypto_utils
from designate import exceptions


class CryptoUtilsTestCase(oslotest.base.BaseTestCase):

    def _create_temp_cert(self, key, no_prehash=False):
        """Generate a self-signed certificate and write it to a temp file."""
        import datetime

        subject = issuer = x509.Name([
            x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, 'test'),
        ])
        now = timeutils.utcnow()
        sign_algorithm = None if no_prehash else hashes.SHA256()
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=1))
            .sign(key, sign_algorithm)
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        fd, path = tempfile.mkstemp(suffix='.pem')
        os.write(fd, cert_pem)
        os.close(fd)
        self.addCleanup(os.unlink, path)
        return path

    def test_is_quantum_vulnerable_cert_rsa(self):
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        path = self._create_temp_cert(key)
        algo, is_vulnerable = crypto_utils.is_quantum_vulnerable_cert(path)
        self.assertEqual('RSA', algo)
        self.assertTrue(is_vulnerable)

    def test_is_quantum_vulnerable_cert_ecdsa(self):
        key = ec.generate_private_key(ec.SECP256R1())
        path = self._create_temp_cert(key)
        algo, is_vulnerable = crypto_utils.is_quantum_vulnerable_cert(path)
        self.assertEqual('ECDSA', algo)
        self.assertTrue(is_vulnerable)

    def test_is_quantum_vulnerable_cert_dsa(self):
        key = dsa.generate_private_key(key_size=2048)
        path = self._create_temp_cert(key)
        algo, is_vulnerable = crypto_utils.is_quantum_vulnerable_cert(path)
        self.assertEqual('DSA', algo)
        self.assertTrue(is_vulnerable)

    def test_is_quantum_vulnerable_cert_ed25519(self):
        key = ed25519.Ed25519PrivateKey.generate()
        path = self._create_temp_cert(key, no_prehash=True)
        algo, is_vulnerable = crypto_utils.is_quantum_vulnerable_cert(path)
        self.assertEqual('Ed25519', algo)
        self.assertTrue(is_vulnerable)

    def test_is_quantum_vulnerable_cert_unsupported_algorithm(self):
        fake_cert = mock.Mock()
        fake_cert.public_key.side_effect = UnsupportedAlgorithm('nope')

        fd, path = tempfile.mkstemp(suffix='.pem')
        os.write(fd, b'irrelevant, load_pem is mocked below')
        os.close(fd)
        self.addCleanup(os.unlink, path)

        with mock.patch.object(
            crypto_utils.x509, 'load_pem_x509_certificate',
            return_value=fake_cert
        ):
            algo, is_vulnerable = crypto_utils.is_quantum_vulnerable_cert(
                path
            )
        self.assertIsNone(algo)
        self.assertIsNone(is_vulnerable)

    def test_is_quantum_vulnerable_cert_file_not_found(self):
        algo, is_vulnerable = crypto_utils.is_quantum_vulnerable_cert(
            '/nonexistent/cert.pem'
        )
        self.assertIsNone(algo)
        self.assertIsNone(is_vulnerable)

    def test_is_quantum_vulnerable_cert_invalid_cert(self):
        fd, path = tempfile.mkstemp(suffix='.pem')
        os.write(fd, b'not a certificate')
        os.close(fd)
        self.addCleanup(os.unlink, path)

        algo, is_vulnerable = crypto_utils.is_quantum_vulnerable_cert(path)
        self.assertIsNone(algo)
        self.assertIsNone(is_vulnerable)

    def test_check_pqc_compliance_disabled(self):
        with mock.patch.object(
            crypto_utils, 'is_quantum_vulnerable_cert'
        ) as mock_check:
            crypto_utils.check_pqc_compliance(
                cert_paths=['/some/cert.pem'],
                check_mode='disabled',
                component_name='test'
            )
            mock_check.assert_not_called()

    def test_check_pqc_compliance_permissive_logs_warning(self):
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        path = self._create_temp_cert(key)

        with mock.patch.object(crypto_utils, 'LOG') as mock_log:
            crypto_utils.check_pqc_compliance(
                cert_paths=[path],
                check_mode='permissive',
                component_name='test-backend'
            )
            mock_log.warning.assert_called_once()
            call_args = mock_log.warning.call_args
            self.assertIn('RSA', str(call_args))
            self.assertIn('quantum-vulnerable', str(call_args))

    def test_check_pqc_compliance_strict_raises(self):
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        path = self._create_temp_cert(key)

        self.assertRaises(
            exceptions.ConfigurationError,
            crypto_utils.check_pqc_compliance,
            cert_paths=[path],
            check_mode='strict',
            component_name='test-backend'
        )

    def test_check_pqc_compliance_strict_raises_on_unparseable_cert(self):
        fd, path = tempfile.mkstemp(suffix='.pem')
        os.write(fd, b'not a certificate')
        os.close(fd)
        self.addCleanup(os.unlink, path)

        self.assertRaises(
            exceptions.ConfigurationError,
            crypto_utils.check_pqc_compliance,
            cert_paths=[path],
            check_mode='strict',
            component_name='test-backend'
        )

    def test_check_pqc_compliance_strict_raises_on_missing_cert(self):
        self.assertRaises(
            exceptions.ConfigurationError,
            crypto_utils.check_pqc_compliance,
            cert_paths=['/nonexistent/cert.pem'],
            check_mode='strict',
            component_name='test-backend'
        )

    def test_check_pqc_compliance_permissive_unparseable_cert_no_raise(self):
        fd, path = tempfile.mkstemp(suffix='.pem')
        os.write(fd, b'not a certificate')
        os.close(fd)
        self.addCleanup(os.unlink, path)

        crypto_utils.check_pqc_compliance(
            cert_paths=[path],
            check_mode='permissive',
            component_name='test-backend'
        )

    def test_check_tls_version_support_1_2(self):
        crypto_utils.check_tls_version_support('1.2')

    def test_check_tls_version_support_invalid(self):
        self.assertRaises(
            exceptions.ConfigurationError,
            crypto_utils.check_tls_version_support,
            '1.0'
        )

    def test_check_tls_version_support_1_3_no_support(self):
        with mock.patch.object(crypto_utils.ssl, 'HAS_TLSv1_3', False):
            self.assertRaises(
                exceptions.ConfigurationError,
                crypto_utils.check_tls_version_support,
                '1.3'
            )
