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

import re
import time

import sqlalchemy
from sqlalchemy.exc import DisconnectionError, OperationalError
import sqlalchemy.orm
from sqlalchemy.pool import NullPool, StaticPool

from oslo.config import cfg
from designate.openstack.common import log as logging
from designate.openstack.common.gettextutils import _

LOG = logging.getLogger(__name__)

_MAKERS = {}
_ENGINES = {}


SQLOPTS = [
    cfg.StrOpt('database_connection',
               default='sqlite:///$state_path/designate.sqlite',
               secret=True,
               help='The database driver to use'),
    cfg.IntOpt('connection_debug', default=0,
               help='Verbosity of SQL debugging information. 0=None,'
               ' 100=Everything'),
    cfg.BoolOpt('connection_trace', default=False,
                help='Add python stack traces to SQL as comment strings'),
    cfg.BoolOpt('sqlite_synchronous', default=True,
                help='If passed, use synchronous mode for sqlite'),
    cfg.IntOpt('idle_timeout', default=3600,
               help='timeout before idle sql connections are reaped'),
    cfg.IntOpt('max_retries', default=10,
               help='maximum db connection retries during startup. '
               '(setting -1 implies an infinite retry count)'),
    cfg.IntOpt('retry_interval', default=10,
               help='interval between retries of opening a sql connection')
]


def get_session(config_group,
                autocommit=True,
                expire_on_commit=False,
                autoflush=True):
    """Return a SQLAlchemy session."""
    global _MAKERS

    if config_group not in _MAKERS:
        engine = get_engine(config_group)
        _MAKERS[config_group] = get_maker(engine,
                                          autocommit,
                                          expire_on_commit,
                                          autoflush)

    session = _MAKERS[config_group]()
    return session


def synchronous_switch_listener(dbapi_conn, connection_rec):
    """Switch sqlite connections to non-synchronous mode"""
    dbapi_conn.execute("PRAGMA synchronous = OFF")


def add_regexp_listener(dbapi_con, con_record):
    """Add REGEXP function to sqlite connections."""

    def regexp(expr, item):
        reg = re.compile(expr)
        return reg.search(unicode(item)) is not None
    dbapi_con.create_function('regexp', 2, regexp)


def ping_listener(dbapi_conn, connection_rec, connection_proxy):
    """
    Ensures that MySQL connections checked out of the
    pool are alive.

    Borrowed from:
    http://groups.google.com/group/sqlalchemy/msg/a4ce563d802c929f
    """
    try:
        dbapi_conn.cursor().execute('select 1')
    except dbapi_conn.OperationalError as ex:
        if ex.args[0] in (2006, 2013, 2014, 2045, 2055):
            LOG.warn('Got mysql server has gone away: %s', ex)
            raise DisconnectionError("Database server went away")
        else:
            raise


def is_db_connection_error(args):
    """Return True if error in connecting to db."""
    # NOTE(adam_g): This is currently MySQL specific and needs to be extended
    #               to support Postgres and others.
    conn_err_codes = ('2002', '2003', '2006')
    for err_code in conn_err_codes:
        if args.find(err_code) != -1:
            return True
    return False


def get_engine(config_group):
    """Return a SQLAlchemy engine."""
    global _ENGINES

    database_connection = cfg.CONF[config_group].database_connection

    if config_group not in _ENGINES:
        connection_dict = sqlalchemy.engine.url.make_url(
            database_connection)

        engine_args = {
            "pool_recycle": cfg.CONF[config_group].idle_timeout,
            "echo": False,
            'convert_unicode': True,
        }

        # Map our SQL debug level to SQLAlchemy's options
        if cfg.CONF[config_group].connection_debug >= 100:
            engine_args['echo'] = 'debug'
        elif cfg.CONF[config_group].connection_debug >= 50:
            engine_args['echo'] = True

        if "sqlite" in connection_dict.drivername:
            engine_args["poolclass"] = NullPool

            if database_connection == "sqlite://":
                engine_args["poolclass"] = StaticPool
                engine_args["connect_args"] = {'check_same_thread': False}

        _ENGINES[config_group] = sqlalchemy.create_engine(database_connection,
                                                          **engine_args)

        if 'mysql' in connection_dict.drivername:
            sqlalchemy.event.listen(_ENGINES[config_group],
                                    'checkout',
                                    ping_listener)
        elif "sqlite" in connection_dict.drivername:
            if not cfg.CONF[config_group].sqlite_synchronous:
                sqlalchemy.event.listen(_ENGINES[config_group],
                                        'connect',
                                        synchronous_switch_listener)
            sqlalchemy.event.listen(_ENGINES[config_group],
                                    'connect',
                                    add_regexp_listener)

        if (cfg.CONF[config_group].connection_trace and
                _ENGINES[config_group].dialect.dbapi.__name__ == 'MySQLdb'):
            import MySQLdb.cursors
            _do_query = debug_mysql_do_query()
            setattr(MySQLdb.cursors.BaseCursor, '_do_query', _do_query)

        try:
            _ENGINES[config_group].connect()
        except OperationalError as e:
            if not is_db_connection_error(e.args[0]):
                raise

            remaining = cfg.CONF[config_group].max_retries
            if remaining == -1:
                remaining = 'infinite'
            while True:
                msg = _('SQL connection failed. %s attempts left.')
                LOG.warn(msg % remaining)
                if remaining != 'infinite':
                    remaining -= 1
                time.sleep(cfg.CONF[config_group].retry_interval)
                try:
                    _ENGINES[config_group].connect()
                    break
                except OperationalError as e:
                    if (remaining != 'infinite' and remaining == 0) or \
                            not is_db_connection_error(e.args[0]):
                        raise
    return _ENGINES[config_group]


def get_maker(engine, autocommit=True, expire_on_commit=False, autoflush=True):
    """Return a SQLAlchemy sessionmaker using the given engine."""
    return sqlalchemy.orm.sessionmaker(bind=engine,
                                       autocommit=autocommit,
                                       autoflush=autoflush,
                                       expire_on_commit=expire_on_commit)


def debug_mysql_do_query():
    """Return a debug version of MySQLdb.cursors._do_query"""
    import MySQLdb.cursors
    import traceback

    old_mysql_do_query = MySQLdb.cursors.BaseCursor._do_query

    def _do_query(self, q):
        stack = ''
        for file, line, method, function in traceback.extract_stack():
            # exclude various common things from trace
            if file.endswith('session.py') and method == '_do_query':
                continue
            if file.endswith('api.py') and method == 'wrapper':
                continue
            if file.endswith('utils.py') and method == '_inner':
                continue
            if file.endswith('exception.py') and method == '_wrap':
                continue
            # nova/db/api is just a wrapper around nova/db/sqlalchemy/api
            if file.endswith('nova/db/api.py'):
                continue
            # only trace inside nova
            index = file.rfind('nova')
            if index == -1:
                continue
            stack += "File:%s:%s Method:%s() Line:%s | " \
                     % (file[index:], line, method, function)

        # strip trailing " | " from stack
        if stack:
            stack = stack[:-3]
            qq = "%s /* %s */" % (q, stack)
        else:
            qq = q
        old_mysql_do_query(self, qq)

    # return the new _do_query method
    return _do_query
