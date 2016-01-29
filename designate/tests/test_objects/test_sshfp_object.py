# Copyright 2016 Rackspace
#
# Author: Rahman Syed <rahman.syed@gmail.com>
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

from oslo_log import log as logging
import oslotest.base

from designate import objects
from designate.exceptions import InvalidObject

LOG = logging.getLogger(__name__)


def debug(*a, **kw):
    for v in a:
        LOG.debug(repr(v))

    for k in sorted(kw):
        LOG.debug("%s: %s", k, repr(kw[k]))


class SSHFPecordTest(oslotest.base.BaseTestCase):

    def test_parse_sshfp(self):
        sshfp_record = objects.SSHFP()
        sshfp_record._from_string(
                '0 0 72d30d211ce8c464de2811e534de23b9be9b4dc4')

        self.assertEqual(0, sshfp_record.algorithm)
        self.assertEqual(0, sshfp_record.fp_type)
        self.assertEqual('72d30d211ce8c464de2811e534de23b9be9b4dc4',
                         sshfp_record.fingerprint)

    def test_validate_sshfp_signed_zero_alg(self):
        rs = objects.RecordSet(
                name='www.example.org.', type='SSHFP',
                records=objects.RecordList(objects=[
                    objects.Record(
                        data='-0 0 72d30d211ce8c464de2811e534de23b9be9b4dc4',
                        status='ACTIVE'),
                ])
        )

        self.assertRaises(InvalidObject, rs.validate)

    def test_validate_sshfp_signed_zero_fptype(self):
        rs = objects.RecordSet(
                name='www.example.org.', type='SSHFP',
                records=objects.RecordList(objects=[
                    objects.Record(
                        data='0 -0 72d30d211ce8c464de2811e534de23b9be9b4dc4',
                        status='ACTIVE'),
                ])
        )

        self.assertRaises(InvalidObject, rs.validate)
