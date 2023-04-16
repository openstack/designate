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

import copy
import functools
import threading
import time

from oslo_db import exception as db_exception
from oslo_log import log as logging
from oslo_utils import excutils

from designate.storage import sql
from designate.storage import sqlalchemy


LOG = logging.getLogger(__name__)
RETRY_STATE = threading.local()


def get_storage():
    """Return the engine class"""
    return sqlalchemy.SQLAlchemyStorage()


def _retry_on_deadlock(exc):
    """Filter to trigger retry a when a Deadlock is received."""
    # TODO(kiall): This is a total leak of the SQLA Driver, we'll need a better
    #              way to handle this.
    if isinstance(exc, db_exception.DBDeadlock):
        LOG.warning("Deadlock detected. Retrying...")
        return True
    return False


def retry(cb=None, retries=150, delay=50, deep_copy=True):
    """A retry decorator that ignores attempts at creating nested retries"""
    def outer(f):
        @functools.wraps(f)
        def retry_wrapper(self, *args, **kwargs):
            if not hasattr(RETRY_STATE, 'held'):
                # Create the state vars if necessary
                RETRY_STATE.held = False
                RETRY_STATE.retries = 0

            if not RETRY_STATE.held:
                # We're the outermost retry decorator
                RETRY_STATE.held = True

                try:
                    while True:
                        try:
                            if deep_copy:
                                result = f(self, *copy.deepcopy(args),
                                           **copy.deepcopy(kwargs))
                            else:
                                # perform shallow copy
                                result = f(self, *copy.copy(args),
                                           **copy.copy(kwargs))
                            break
                        except Exception as exc:
                            RETRY_STATE.retries += 1
                            if RETRY_STATE.retries >= retries:
                                # Exceeded retry attempts, raise.
                                raise
                            elif cb is not None and cb(exc) is False:
                                # We're not setup to retry on this exception.
                                raise
                            else:
                                # Retry, with a delay.
                                time.sleep(delay / float(1000))

                finally:
                    RETRY_STATE.held = False
                    RETRY_STATE.retries = 0

            else:
                # We're an inner retry decorator, just pass on through.
                if deep_copy:
                    result = f(self, *copy.deepcopy(args),
                               **copy.deepcopy(kwargs))
                else:
                    # perform shallow copy
                    result = f(self, *copy.copy(args),
                               **copy.copy(kwargs))

            return result
        retry_wrapper.__wrapped_function = f
        retry_wrapper.__wrapper_name = 'retry'
        return retry_wrapper
    return outer


def transaction(f):
    """Transaction decorator, to be used on class instances with a
    self.storage attribute
    """

    @retry(cb=_retry_on_deadlock)
    @functools.wraps(f)
    def transaction_wrapper(self, *args, **kwargs):
        with sql.get_write_session() as session:
            # session.begin()
            try:
                result = f(self, *args, **kwargs)
                # session.commit()
                return result
            except Exception:
                with excutils.save_and_reraise_exception():
                    session.rollback()

    transaction_wrapper.__wrapped_function = f
    transaction_wrapper.__wrapper_name = 'transaction'
    return transaction_wrapper


def transaction_shallow_copy(f):
    """Transaction decorator, to be used on class instances with a
    self.storage attribute where shallow copy of args, kwargs is used
    """
    @retry(cb=_retry_on_deadlock, deep_copy=False)
    @functools.wraps(f)
    def transaction_wrapper(self, *args, **kwargs):
        with sql.get_write_session() as session:
            # session.begin()
            try:
                result = f(self, *args, **kwargs)
                # session.commit()
                return result
            except Exception:
                with excutils.save_and_reraise_exception():
                    session.rollback()

    transaction_wrapper.__wrapped_function = f
    transaction_wrapper.__wrapper_name = 'transaction_shallow_copy'
    return transaction_wrapper
