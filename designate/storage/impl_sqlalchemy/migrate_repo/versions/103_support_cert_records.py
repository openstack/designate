# Copyright 2021 Cloudification GmbH
#
# Author: cloudification <contact@cloudification.io>
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

from sqlalchemy import MetaData, Table, Enum

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                    'PTR', 'SSHFP', 'SOA', 'NAPTR', 'CAA', 'CERT']

    records_table = Table('recordsets', meta, autoload=True)
    records_table.columns.type.alter(name='type', type=Enum(*RECORD_TYPES))
