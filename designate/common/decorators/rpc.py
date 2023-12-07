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

import functools
import inspect
import threading

from oslo_messaging.rpc import dispatcher as rpc_dispatcher

import designate.exceptions


RPC_LOGGING_DISALLOW = [
    'get_instance',
    '__init__'
]


class ExceptionThreadLocal(threading.local):
    def __init__(self):
        super().__init__()
        self.depth = 0

    def reset_depth(self):
        self.depth = 0


def expected_exceptions():
    def outer(f):
        @functools.wraps(f)
        def exception_wrapper(cls, *args, **kwargs):
            cls.exception_thread_local.depth += 1

            # We only want to wrap the first function wrapped.
            if cls.exception_thread_local.depth > 1:
                return f(cls, *args, **kwargs)

            try:
                return f(cls, *args, **kwargs)
            except designate.exceptions.DesignateException as e:
                if e.expected:
                    raise rpc_dispatcher.ExpectedException()
                raise
            finally:
                cls.exception_thread_local.reset_depth()
        return exception_wrapper
    return outer


def log_rpc_call(func, rpcapi, logger):
    def wrapped(*args, **kwargs):
        logger.debug(
            'Calling designate.%(rpcapi)s.%(function)s() over RPC',
            {
                'function': func.__name__,
                'rpcapi': rpcapi
            }
        )
        return func(*args, **kwargs)
    return wrapped


def rpc_logging(logger, rpcapi):
    def wrapper(cls):
        disallow = getattr(cls, 'RPC_LOGGING_DISALLOW', [])
        disallow.extend(RPC_LOGGING_DISALLOW)
        for name, value in inspect.getmembers(cls, inspect.ismethod):
            if name not in disallow:
                setattr(cls, name, log_rpc_call(value, rpcapi, logger))
        return cls
    return wrapper
