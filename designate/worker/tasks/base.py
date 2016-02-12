# Copyright 2016 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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
# under the License.mport threading

from oslo_config import cfg
from oslo_log import log as logging

from designate.central import rpcapi as central_rpcapi
from designate import quota
from designate import storage
from designate import utils
from designate.worker import rpcapi as worker_rpcapi

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class TaskConfig(object):
    """
    Configuration mixin for the various configuration settings that
    a task may want to access
    """
    @property
    def config(self):
        if not hasattr(self, '_config'):
            self._config = CONF['service:worker']
        return self._config

    @property
    def threshold_percentage(self):
        if not hasattr(self, '_threshold_percentage'):
            self._threshold_percentage = self.config.threshold_percentage
        return self._threshold_percentage

    @property
    def timeout(self):
        if not hasattr(self, '_timeout'):
            self._timeout = self.config.poll_timeout
        return self._timeout

    @property
    def retry_interval(self):
        if not hasattr(self, '_retry_interval'):
            self._retry_interval = self.config.poll_retry_interval
        return self._retry_interval

    @property
    def max_retries(self):
        if not hasattr(self, '_max_retries'):
            self._max_retries = self.config.poll_max_retries
        return self._max_retries

    @property
    def delay(self):
        if not hasattr(self, '_delay'):
            self._delay = self.config.poll_delay
        return self._delay

    @property
    def max_prop_time(self):
        # Compute a time (seconds) by which things should have propagated
        if not hasattr(self, '_max_prop_time'):
            self._max_prop_time = utils.max_prop_time(
                self.timeout,
                self.max_retries,
                self.retry_interval,
                self.delay
            )
        return self._max_prop_time


class Task(TaskConfig):
    """
    Base task interface that includes some helpful connections to other
    services and the basic skeleton for tasks.

    Tasks are:
        - Callable
        - Take an executor as their first parameter
        - Can optionally return something
    """
    def __init__(self, executor, **kwargs):
        self.executor = executor
        self.task_name = self.__class__.__name__
        self.options = {}

    @property
    def storage(self):
        if not hasattr(self, '_storage'):
            # Get a storage connection
            storage_driver = cfg.CONF['service:central'].storage_driver
            self._storage = storage.get_storage(storage_driver)
        return self._storage

    @property
    def quota(self):
        if not hasattr(self, '_quota'):
            # Get a quota manager instance
            self._quota = quota.get_quota()
        return self._quota

    @property
    def central_api(self):
        if not hasattr(self, '_central_api'):
            self._central_api = central_rpcapi.CentralAPI.get_instance()
        return self._central_api

    @property
    def worker_api(self):
        if not hasattr(self, '_worker_api'):
            self._worker_api = worker_rpcapi.WorkerAPI.get_instance()
        return self._worker_api

    def __call__(self):
        raise NotImplementedError
