# Copyright 2018 Canonical Ltd.
#
# Author: Tytus Kurek <tytus.kurek@canonical.com>
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

from oslo_log import log as logging
import oslotest.base

from designate import objects

LOG = logging.getLogger(__name__)


def debug(*a, **kw):
    for v in a:
        LOG.debug(repr(v))

    for k in sorted(kw):
        LOG.debug("%s: %s", k, repr(kw[k]))


class CAARecordTest(oslotest.base.BaseTestCase):

    def test_parse_caa_issue(self):
        caa_record = objects.CAA()
        caa_record._from_string('0 issue ca.example.net')

        self.assertEqual(0, caa_record.flags)
        self.assertEqual('issue ca.example.net', caa_record.prpt)

    def test_parse_caa_issuewild(self):
        caa_record = objects.CAA()
        caa_record._from_string('1 issuewild ca.example.net; policy=ev')

        self.assertEqual(1, caa_record.flags)
        self.assertEqual('issuewild ca.example.net; policy=ev',
                         caa_record.prpt)

    def test_parse_caa_iodef(self):
        caa_record = objects.CAA()
        caa_record._from_string('0 iodef https://example.net/')

        self.assertEqual(0, caa_record.flags)
        self.assertEqual('iodef https://example.net/', caa_record.prpt)
