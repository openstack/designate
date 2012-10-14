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
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging

LOG = logging.getLogger(__name__)
_ENGINE = None
_SESSION = None


def get_session():
    global _ENGINE, _SESSION

    if _ENGINE is None:
        _ENGINE = get_engine()

    if _SESSION is None:
        Session = sessionmaker(bind=_ENGINE, autocommit=True,
                               expire_on_commit=False)
        _SESSION = scoped_session(Session)

    return _SESSION


def get_engine():
    url = cfg.CONF.sql_connection

    engine_args = {
        'echo': False,
        'convert_unicode': True,
    }

    if cfg.CONF.verbose or cfg.CONF.debug:
        engine_args['echo'] = True
    engine = create_engine(url, **engine_args)

    engine.connect()

    return engine


def reset_session():
    global _ENGINE, _SESSION

    _ENGINE = None
    _SESSION = None
