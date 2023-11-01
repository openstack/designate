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
from io import StringIO
import os
import sys

from alembic import command as alembic_command
from alembic.config import Config
from oslo_log import log as logging

import designate.conf
from designate.manage import base

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class DatabaseCommands(base.Commands):
    def _get_alembic_config(self, db_url=None, stringio_buffer=sys.stdout):
        alembic_dir = os.path.join(os.path.dirname(__file__),
                                   os.pardir, 'storage/sqlalchemy')
        alembic_cfg = Config(os.path.join(alembic_dir, 'alembic.ini'),
                             stdout=stringio_buffer)
        alembic_cfg.set_main_option(
            'script_location', 'designate.storage.sqlalchemy:alembic')
        if db_url:
            alembic_cfg.set_main_option('sqlalchemy.url', db_url)
        else:
            alembic_cfg.set_main_option('sqlalchemy.url',
                                        CONF['storage:sqlalchemy'].connection)
        return alembic_cfg

    def current(self, db_url=None, stringio_buffer=sys.stdout):
        alembic_command.current(
            self._get_alembic_config(db_url=db_url,
                                     stringio_buffer=stringio_buffer))

    def heads(self, db_url=None, stringio_buffer=sys.stdout):
        alembic_command.heads(
            self._get_alembic_config(db_url=db_url,
                                     stringio_buffer=stringio_buffer))

    def history(self, db_url=None, stringio_buffer=sys.stdout):
        alembic_command.history(
            self._get_alembic_config(db_url=db_url,
                                     stringio_buffer=stringio_buffer))

    def version(self, db_url=None):
        # Using StringIO buffers here to keep the command output as similar
        # as it was before the migration to alembic.
        current_buffer = StringIO()
        latest_buffer = StringIO()
        alembic_command.current(
            self._get_alembic_config(db_url=db_url,
                                     stringio_buffer=current_buffer))
        current = current_buffer.getvalue().replace('\n', ' ')
        current_buffer.close()
        alembic_command.heads(
            self._get_alembic_config(db_url=db_url,
                                     stringio_buffer=latest_buffer))
        latest = latest_buffer.getvalue().replace('\n', ' ')
        latest_buffer.close()
        print(f'Current: {current} Latest: {latest}')

    def sync(self, db_url=None, stringio_buffer=sys.stdout):
        alembic_command.upgrade(
            self._get_alembic_config(db_url=db_url,
                                     stringio_buffer=stringio_buffer), 'head')

    @base.args('revision', default='head', nargs='?',
               help='The revision identifier to upgrade to.')
    def upgrade(self, revision, db_url=None, stringio_buffer=sys.stdout):
        alembic_command.upgrade(
            self._get_alembic_config(
                db_url=db_url, stringio_buffer=stringio_buffer), revision)
