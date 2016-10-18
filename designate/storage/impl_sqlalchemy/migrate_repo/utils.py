# Copyright 2012 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
# Author: Patrick Galbraith <patg@hp.com>
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

"""
Various conveniences used for migration scripts
"""
from oslo_log import log as logging
from sqlalchemy.schema import Table as SqlaTable


LOG = logging.getLogger(__name__)


def create_tables(tables):
    for table in tables:
        LOG.debug("Creating table %s" % table)
        table.create()


def drop_tables(tables):
    for table in tables:
        LOG.debug("Dropping table %s" % table)
        table.drop()


def Table(*args, **kwargs):
    if 'mysql_engine' not in kwargs:
        kwargs['mysql_engine'] = 'INNODB'

    return SqlaTable(*args, **kwargs)
