# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hp.com>
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

import unittest

from oslo_log import log as logging
from testtools import ExpectedException as raises  # with raises(...): ...
import mock
import oslotest.base

from designate import exceptions
from designate import objects

LOG = logging.getLogger(__name__)


def create_test_domain():
    return objects.Domain(
        name='www.example.org.',
        email='foo@example.com',
    )


class DomainTest(oslotest.base.BaseTestCase):

    def test_init(self):
        domain = create_test_domain()
        self.assertEqual(domain.name, 'www.example.org.')

    def test_masters_none(self):
        domain = objects.Domain()
        self.assertEqual(domain.masters, None)

    def test_masters(self):
        domain = objects.Domain(
            attributes=objects.DomainAttributeList.from_list([
                objects.DomainAttribute(key='master', value='1.0.0.0')
            ])
        )
        self.assertEqual(domain.masters, ['1.0.0.0'])

    def test_masters_2(self):
        domain = objects.Domain(
            attributes=objects.DomainAttributeList.from_list([
                objects.DomainAttribute(key='master', value='1.0.0.0'),
                objects.DomainAttribute(key='master', value='2.0.0.0')
            ])
        )
        self.assertEqual(len(domain.masters), 2)

    def test_set_masters_none(self):
        domain = create_test_domain()
        domain.set_masters(('1.0.0.0', '2.0.0.0'))
        self.assertEqual(len(domain.attributes), 2)

    def test_get_master_by_ip(self):
        domain = objects.Domain(
            attributes=objects.DomainAttributeList.from_list([
                objects.DomainAttribute(key='master', value='1.0.0.0'),
                objects.DomainAttribute(key='master', value='2.0.0.0')
            ])
        )

        def mock_split(v):
            assert ':' not in v
            return v, ''

        with mock.patch('designate.objects.domain.utils.split_host_port',
                        side_effect=mock_split):
            m = domain.get_master_by_ip('2.0.0.0')

        self.assertEqual(m, '2.0.0.0')

    @unittest.expectedFailure  # bug: domain.masters is not iterable
    def test_get_master_by_ip_none(self):
        domain = objects.Domain()
        m = domain.get_master_by_ip('2.0.0.0')
        self.assertEqual(m, False)

    def test_validate(self):
        domain = create_test_domain()
        domain.validate()

    def test_validate_invalid_secondary(self):
        domain = objects.Domain(
            type='SECONDARY',
        )
        with raises(exceptions.InvalidObject):
            domain.validate()
