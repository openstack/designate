#
# Copyright (C) 2016 Red Hat, Inc.
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
#

from designate.i18n import _LE

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class NoopConnection(object):
    def __init__(self):
        pass

    def _flush_buffer(self):
        pass

    def close_buffer(self):
        pass

    def connect(self, *a, **kw):
        LOG.error(_LE('Using noop metrics client. Metrics will be ignored.'))
        pass

    def open_buffer(self):
        pass


class NoopCounter(object):
    def __init__(self):
        pass

    def increment(self, *a, **kw):
        pass

    def decrement(self, *a, **kw):
        pass

    def __add__(self, value):
        pass

    def __sub__(self, value):
        pass


class NoopGauge(object):
    def __init__(self):
        pass

    def send(self, *a, **kw):
        pass


class NoopTimer(object):
    def __init__(self):
        pass

    def timed(self, *a, **kw):
        def wrapper(func):
            return func
        return wrapper


class Client(object):
    def __init__(self, *a, **kw):
        self._counter = NoopCounter()
        self._gauge = NoopGauge()
        self._timer = NoopTimer()
        self.connection = NoopConnection()
        pass

    def get_counter(self, *a, **kw):
        return self._counter

    def get_gauge(self, *a, **kw):
        return self._gauge

    def get_timer(self):
        return self._timer
