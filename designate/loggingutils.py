# Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

import inspect

LOG = {}


def log_rpc_call(func, rpcapi, logger):
    def wrapped(*args, **kwargs):
        logger.debug("Calling designate.%(rpcapi)s.%(function)s() "
                     "over RPC", {'function': func.__name__,
                                  'rpcapi': rpcapi})
        return func(*args, **kwargs)
    return wrapped


LOGGING_BLACKLIST = [
    'get_instance',
    '__init__'
]


def rpc_logging(logger, rpcapi):
    def wrapper(cls):
        CLASS_BLACKLIST = getattr(cls, 'LOGGING_BLACKLIST', [])
        BLACKLIST = CLASS_BLACKLIST + LOGGING_BLACKLIST
        for name, m in inspect.getmembers(cls, inspect.ismethod):
            if name not in BLACKLIST:
                setattr(cls, name, log_rpc_call(m, rpcapi, logger))
        return cls
    return wrapper
