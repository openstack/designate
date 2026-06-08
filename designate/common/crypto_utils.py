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
import ssl

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric import ed448
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.asymmetric import x448
from cryptography import x509
from oslo_log import log as logging

from designate.common import constants
from designate import exceptions


LOG = logging.getLogger(__name__)

TLS_VERSION_MAP = {
    '1.2': ssl.TLSVersion.TLSv1_2,
    '1.3': ssl.TLSVersion.TLSv1_3,
}

# Ed25519/Ed448 (EdDSA) and X25519/X448 (ECDH) rely on the same elliptic
# curve discrete logarithm problem as ECDSA, so they are broken by Shor's
# algorithm just like RSA/ECDSA/DSA and are not a PQC-safe alternative.
QUANTUM_VULNERABLE_NAMES = {
    rsa.RSAPublicKey: 'RSA',
    ec.EllipticCurvePublicKey: 'ECDSA',
    dsa.DSAPublicKey: 'DSA',
    ed25519.Ed25519PublicKey: 'Ed25519',
    ed448.Ed448PublicKey: 'Ed448',
    x25519.X25519PublicKey: 'X25519',
    x448.X448PublicKey: 'X448',
}


def is_quantum_vulnerable_cert(cert_path):
    """Load a certificate and classify its public key algorithm.

    :param cert_path: Path to a PEM or DER encoded certificate file.
    :returns: Tuple of (algorithm_name, is_quantum_vulnerable).
              Returns (None, None) if the certificate cannot be loaded.
    """
    try:
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
    except (OSError, IOError):
        LOG.warning('PQC check: unable to read certificate file %s',
                    cert_path)
        return None, None

    try:
        cert = x509.load_pem_x509_certificate(cert_data)
    except ValueError:
        try:
            cert = x509.load_der_x509_certificate(cert_data)
        except ValueError:
            LOG.warning('PQC check: unable to parse certificate file %s',
                        cert_path)
            return None, None

    try:
        pub_key = cert.public_key()
    except UnsupportedAlgorithm:
        LOG.warning(
            'PQC check: certificate %s uses a public key algorithm '
            'that could not be classified', cert_path
        )
        return None, None

    for key_type, name in QUANTUM_VULNERABLE_NAMES.items():
        if isinstance(pub_key, key_type):
            return name, True

    return type(pub_key).__name__, False


def check_pqc_compliance(cert_paths, check_mode, component_name):
    """Run PQC compliance checks on certificate files.

    :param cert_paths: List of certificate file paths to check.
    :param check_mode: One of constants.PQC_MODE_DISABLED,
                       constants.PQC_MODE_PERMISSIVE,
                       constants.PQC_MODE_STRICT.
    :param component_name: Name of the component for log messages.
    :raises: ConfigurationError in strict mode for vulnerable certs.
    """
    if check_mode == constants.PQC_MODE_DISABLED:
        return

    for cert_path in cert_paths:
        if not cert_path:
            continue

        algorithm, is_vulnerable = is_quantum_vulnerable_cert(cert_path)
        if algorithm is None:
            if check_mode == constants.PQC_MODE_STRICT:
                raise exceptions.ConfigurationError(
                    '%s: certificate %s could not be read or parsed; '
                    'refusing to start in strict PQC check mode.' %
                    (component_name, cert_path)
                )
            continue

        if is_vulnerable:
            msg = (
                '%(component)s: certificate %(path)s uses %(algo)s, '
                'which is quantum-vulnerable. Consider migrating to a '
                'post-quantum algorithm (e.g., ML-DSA) when supported '
                'by the platform.'
            )
            args = {
                'component': component_name,
                'path': cert_path,
                'algo': algorithm,
            }

            if check_mode == constants.PQC_MODE_STRICT:
                raise exceptions.ConfigurationError(msg % args)

            LOG.warning(msg, args)


def check_tls_version_support(version_str):
    """Verify that the requested TLS version is supported.

    :param version_str: TLS version string ('1.2' or '1.3').
    :raises: ConfigurationError if the version is not supported.
    """
    if version_str not in TLS_VERSION_MAP:
        raise exceptions.ConfigurationError(
            'Unsupported TLS version: %s. '
            'Supported values: %s' % (version_str,
                                      ', '.join(TLS_VERSION_MAP))
        )

    if version_str == '1.3' and not getattr(ssl, 'HAS_TLSv1_3', False):
        raise exceptions.ConfigurationError(
            'TLS 1.3 is required but not supported by the installed '
            'OpenSSL library. Upgrade OpenSSL to 1.1.1+ to enable '
            'TLS 1.3 and PQC key exchange support.'
        )
