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
from oslo_config import cfg

PQC_GROUP = cfg.OptGroup(
    name='pqc',
    title='Post-Quantum Cryptography Readiness Options'
)

PQC_OPTS = [
    cfg.StrOpt(
        'check_mode',
        default='permissive',
        choices=[
            ('disabled',
             'No PQC compliance checks are performed.'),
            ('permissive',
             'Emit warnings at startup if quantum-vulnerable '
             'certificate algorithms or weak TSIG algorithms '
             'are detected. Service startup is not blocked. '
             'This is the default: it does not change any '
             'existing behavior, it only adds visibility.'),
            ('strict',
             'Refuse to start if quantum-vulnerable certificate '
             'algorithms are detected in configured TLS '
             'certificate files.'),
        ],
        help='Controls how Designate validates cryptographic '
             'algorithm choices at startup. Quantum-vulnerable '
             'algorithms include RSA, ECDSA, and DSA for '
             'asymmetric operations. PQC key exchange requires '
             'TLS 1.3. This option applies to all backends that '
             'use TLS for control-plane communication. Set to '
             '"disabled" to silence these checks entirely.'
    ),
    cfg.StrOpt(
        'tls_minimum_version',
        default=None,
        choices=[
            (None, 'Use the system default TLS version.'),
            ('1.2', 'Require TLS 1.2 as the minimum version.'),
            ('1.3', 'Require TLS 1.3 as the minimum version. '
                    'Required for PQC key exchange support.'),
        ],
        help='Set the minimum TLS protocol version for backend '
             'connections that use direct TLS (currently NSD4). '
             'When set, this overrides the system default. '
             'Has no effect on backends that use the requests '
             'library (PDNS4, NS1, etc.) as those rely on system '
             'OpenSSL configuration.'
    ),
]


def register_opts(conf):
    conf.register_group(PQC_GROUP)
    conf.register_opts(PQC_OPTS, group=PQC_GROUP)


def list_opts():
    return {
        PQC_GROUP: PQC_OPTS,
    }
