# Copyright 2010 United States Government as represented by the
#   Administrator of the National Aeronautics and Space Administration.
#   All Rights Reserved.
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

"""Session Handling for SQLAlchemy backend."""

import sqlalchemy
import threading

from oslo_config import cfg
from oslo_db import options as db_options
from oslo_db.sqlalchemy import enginefacade
from oslo_log import log as logging
from oslo_utils import importutils
from osprofiler import opts as profiler
from sqlalchemy import inspect

import designate.conf


osprofiler_sqlalchemy = importutils.try_import('osprofiler.sqlalchemy')

CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)

try:
    CONF.import_group('profiler', 'designate.service')
except cfg.NoSuchGroupError:
    pass


_CONTEXT = None
_LOCK = threading.Lock()
_MAIN_CONTEXT_MANAGER = None


def initialize():
    """Initialize the module."""
    connection = CONF['storage:sqlalchemy'].connection
    db_options.set_defaults(
        CONF, connection=connection
    )
    profiler.set_defaults(CONF, enabled=False, trace_sqlalchemy=False)


def _get_main_context_manager():
    global _LOCK
    global _MAIN_CONTEXT_MANAGER

    with _LOCK:
        if not _MAIN_CONTEXT_MANAGER:
            initialize()
            _MAIN_CONTEXT_MANAGER = enginefacade.transaction_context()

    return _MAIN_CONTEXT_MANAGER


def _get_context():
    global _CONTEXT
    if _CONTEXT is None:
        import threading
        _CONTEXT = threading.local()
    return _CONTEXT


def _wrap_session(sess):
    if not osprofiler_sqlalchemy:
        return sess
    if CONF.profiler.enabled and CONF.profiler.trace_sqlalchemy:
        sess = osprofiler_sqlalchemy.wrap_session(sqlalchemy, sess)
    return sess


def get_read_engine():
    return _get_main_context_manager().reader.get_engine()


def get_inspector():
    return inspect(get_read_engine())


def get_read_session():
    reader = _get_main_context_manager().reader
    return _wrap_session(reader.using(_get_context()))


def get_write_session():
    writer = _get_main_context_manager().writer
    return _wrap_session(writer.using(_get_context()))
