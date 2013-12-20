# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement


class InsertFromSelect(Executable, ClauseElement):
    execution_options = \
        Executable._execution_options.union({'autocommit': True})

    def __init__(self, table, select, columns=None):
        self.table = table
        self.select = select
        self.columns = columns


@compiles(InsertFromSelect)
def visit_insert_from_select(element, compiler, **kw):
    # NOTE(kiall): SQLA 0.8.3+ has an InsertFromSelect built in:
    #              sqlalchemy.sql.expression.Insert.from_select
    #              This code can be removed once we require 0.8.3+
    table = compiler.process(element.table, asfrom=True)
    select = compiler.process(element.select)

    if element.columns is not None:

        columns = [compiler.preparer.format_column(c) for c in element.columns]
        columns = ", ".join(columns)

        return "INSERT INTO %s (%s) %s" % (
            table,
            columns,
            select
        )
    else:
        return "INSERT INTO %s %s" % (
            table,
            select
        )


# # Dialect specific compilation example, should it be needed.
# @compiles(InsertFromSelect, 'postgresql')
# def visit_insert_from_select(element, compiler, **kw):
#     ...
