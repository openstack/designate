# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
from oslo_db import options

STORAGE_GROUP = cfg.OptGroup(
    name='storage:sqlalchemy',
    title="Configuration for SQLAlchemy Storage"
)


def register_opts(conf):
    conf.register_group(STORAGE_GROUP)
    conf.register_opts(options.database_opts, group=STORAGE_GROUP)


def list_opts():
    return {
        STORAGE_GROUP: options.database_opts,
    }
