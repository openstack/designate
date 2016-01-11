# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
import operator

import mock
import sqlalchemy as sa
from sqlalchemy.sql import operators

from designate.sqlalchemy import base
from designate.tests import TestCase

metadata = sa.MetaData()

dummy_table = sa.Table('dummy', metadata,
    sa.Column('id', sa.String(36)),
    sa.Column('a', sa.String()),
    sa.Column('int', sa.Integer()),
)


class SQLAlchemyTestCase(TestCase):
    def setUp(self):
        super(SQLAlchemyTestCase, self).setUp()
        self.query = mock.Mock()

    def test_wildcard(self):
        criterion = {"a": "%foo%"}

        op = dummy_table.c.a.like("%foo")
        with mock.patch.object(dummy_table.c.a, 'operate') as func:
            func.return_value = op

            base.SQLAlchemy._apply_criterion(
                dummy_table, self.query, criterion)
            func.assert_called_with(operators.like_op, "%foo%", escape=None)
            self.query.where.assert_called_with(op)

    def test_ne(self):
        criterion = {"a": "!foo"}

        op = dummy_table.c.a != "foo"
        with mock.patch.object(dummy_table.c.a, 'operate') as func:
            func.return_value = op

            base.SQLAlchemy._apply_criterion(
                dummy_table, self.query, criterion)
            func.assert_called_with(operator.ne, "foo")
            self.query.where.assert_called_with(op)

    def test_le(self):
        criterion = {"a": "<=foo"}

        op = dummy_table.c.a <= "foo"
        with mock.patch.object(dummy_table.c.a, 'operate') as func:
            func.return_value = op

            base.SQLAlchemy._apply_criterion(
                dummy_table, self.query, criterion)
            func.assert_called_with(operator.le, "foo")
            self.query.where.assert_called_with(op)

    def test_lt(self):
        criterion = {"a": "<foo"}

        op = dummy_table.c.a < "foo"
        with mock.patch.object(dummy_table.c.a, 'operate') as func:
            func.return_value = op

            base.SQLAlchemy._apply_criterion(
                dummy_table, self.query, criterion)
            func.assert_called_with(operator.lt, "foo")
            self.query.where.assert_called_with(op)

    def test_ge(self):
        criterion = {"a": ">=foo"}

        op = dummy_table.c.a >= "foo"
        with mock.patch.object(dummy_table.c.a, 'operate') as func:
            func.return_value = op

            base.SQLAlchemy._apply_criterion(
                dummy_table, self.query, criterion)
            func.assert_called_with(operator.ge, "foo")
            self.query.where.assert_called_with(op)

    def test_gt(self):
        criterion = {"a": ">foo"}

        op = dummy_table.c.a > "foo"
        with mock.patch.object(dummy_table.c.a, 'operate') as func:
            func.return_value = op

            base.SQLAlchemy._apply_criterion(
                dummy_table, self.query, criterion)
            func.assert_called_with(operator.gt, "foo")
            self.query.where.assert_called_with(op)

    def test_between(self):
        criterion = {"a": "BETWEEN 1,3"}

        op = dummy_table.c.a.between(1, 3)
        with mock.patch.object(dummy_table.c.a, 'operate') as func:
            func.return_value = op

            base.SQLAlchemy._apply_criterion(
                dummy_table, self.query, criterion)
            func.assert_called_with(operators.between_op, '1', '3',
                                    symmetric=False)
            self.query.where.assert_called_with(op)
