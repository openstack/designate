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
import oslotest.base
import testtools

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
        with testtools.ExpectedException(exceptions.RelationNotLoaded):
            self.assertEqual(domain.masters, None)

    def test_masters(self):
        domain = objects.Domain(
            masters=objects.DomainMasterList.from_list([
                {'host': '1.0.0.0', 'port': 53}
            ])
        )
        self.assertEqual(
            domain.masters.to_list(), [{'host': '1.0.0.0', 'port': 53}])

    def test_masters_2(self):
        domain = objects.Domain(
            masters=objects.DomainMasterList.from_list([
                {'host': '1.0.0.0'},
                {'host': '2.0.0.0'}
            ])
        )
        self.assertEqual(len(domain.masters), 2)

    def test_get_master_by_ip(self):
        domain = objects.Domain(
            masters=objects.DomainMasterList.from_list([
                {'host': '1.0.0.0', 'port': 53},
                {'host': '2.0.0.0', 'port': 53}
            ])
        )
        m = domain.get_master_by_ip('2.0.0.0').to_data()

        self.assertEqual(m, '2.0.0.0:53')

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
        with testtools.ExpectedException(exceptions.InvalidObject):
            domain.validate()

    def test_validate_primary_with_masters(self):
        masters = objects.DomainMasterList()
        masters.append(objects.DomainMaster.from_data("10.0.0.1:53"))
        domain = objects.Domain(
            name='example.com.',
            type='PRIMARY',
            email="foo@example.com",
            masters=masters
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            domain.validate()

    def test_validate_primary_no_email(self):
        masters = objects.DomainMasterList()
        masters.append(objects.DomainMaster.from_data("10.0.0.1:53"))
        domain = objects.Domain(
            name='example.com.',
            type='PRIMARY',
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            domain.validate()

    def test_validate_secondary_with_email(self):
        masters = objects.DomainMasterList()
        masters.append(objects.DomainMaster.from_data("10.0.0.1:53"))
        domain = objects.Domain(
            name='example.com.',
            type='SECONDARY',
            email="foo@example.com",
            masters=masters
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            domain.validate()

    def test_validate_secondary_with_ttl(self):
        masters = objects.DomainMasterList()
        masters.append(objects.DomainMaster.from_data("10.0.0.1:53"))
        domain = objects.Domain(
            name='example.com.',
            type='SECONDARY',
            ttl=600,
            masters=masters
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            domain.validate()

    def test_validate_secondary_with_masters_empty_list(self):
        masters = objects.DomainMasterList()
        domain = objects.Domain(
            name='example.com.',
            type='SECONDARY',
            masters=masters
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            domain.validate()

    def test_validate_secondary_with_masters_none(self):
        domain = objects.Domain(
            name='example.com.',
            type='SECONDARY',
            masters=None
        )
        with testtools.ExpectedException(exceptions.InvalidObject):
            domain.validate()
