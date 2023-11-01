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
from oslo_log import log as logging

from designate.central import rpcapi as central_rpcapi
import designate.conf
from designate import exceptions
from designate import quota
from designate import storage
from designate import utils
from designate.worker import rpcapi as worker_rpcapi


LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF


def percentage(part, whole):
    if whole == 0:
        return 0
    return 100 * float(part) / float(whole)


class TaskConfig:
    """
    Configuration mixin for the various configuration settings that
    a task may want to access
    """
    def __init__(self):
        self._config = None
        self._delay = None
        self._max_prop_time = None
        self._max_retries = None
        self._retry_interval = None
        self._timeout = None
        self._threshold_percentage = None

    @property
    def config(self):
        if not self._config:
            self._config = CONF['service:worker']
        return self._config

    @property
    def threshold_percentage(self):
        if self._threshold_percentage is None:
            self._threshold_percentage = self.config.threshold_percentage
        return self._threshold_percentage

    @property
    def timeout(self):
        if self._timeout is None:
            self._timeout = self.config.poll_timeout
        return self._timeout

    @property
    def retry_interval(self):
        if self._retry_interval is None:
            self._retry_interval = self.config.poll_retry_interval
        return self._retry_interval

    @property
    def max_retries(self):
        if self._max_retries is None:
            self._max_retries = self.config.poll_max_retries
        return self._max_retries

    @property
    def delay(self):
        if self._delay is None:
            self._delay = self.config.poll_delay
        return self._delay

    @property
    def max_prop_time(self):
        # Compute a time (seconds) by which things should have propagated
        if self._max_prop_time is None:
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
        super().__init__()

        self._storage = None
        self._quota = None
        self._central_api = None
        self._worker_api = None
        self._threshold = None

        self.executor = executor
        self.task_name = self.__class__.__name__
        self.options = {}

    @property
    def storage(self):
        if not self._storage:
            self._storage = storage.get_storage()
        return self._storage

    @property
    def quota(self):
        if not self._quota:
            # Get a quota manager instance
            self._quota = quota.get_quota()
        return self._quota

    @property
    def central_api(self):
        if not self._central_api:
            self._central_api = central_rpcapi.CentralAPI.get_instance()
        return self._central_api

    @property
    def worker_api(self):
        if not self._worker_api:
            self._worker_api = worker_rpcapi.WorkerAPI.get_instance()
        return self._worker_api

    @property
    def threshold_percentage(self):
        if self._threshold is None:
            self._threshold = CONF['service:worker'].threshold_percentage
        return self._threshold

    def compare_threshold(self, successes, total):
        return percentage(successes, total) >= self.threshold_percentage

    def is_current_action_valid(self, context, action, zone):
        """Is our current action still valid?"""

        # We always allow for DELETE operations.
        if action == 'DELETE':
            return True

        try:
            zone = self.storage.get_zone(context, zone.id)

            # If the zone is either in a DELETE or NONE state,
            # we don't need to continue with the current action.
            if zone.action in ['DELETE', 'NONE']:
                LOG.info(
                    'Failed to %(action)s zone_name=%(zone_name)s '
                    'zone_id=%(zone_id)s action state has changed '
                    'to %(current_action)s, not retrying action',
                    {
                        'action': action,
                        'zone_name': zone.name,
                        'zone_id': zone.id,
                        'current_action': zone.action,
                    }
                )
                return False
        except exceptions.ZoneNotFound:
            if action != 'CREATE':
                LOG.info(
                    'Failed to %(action)s zone_name=%(zone_name)s '
                    'zone_id=%(zone_id)s Error=ZoneNotFound',
                    {
                        'action': action,
                        'zone_name': zone.name,
                        'zone_id': zone.id,
                    }
                )
                return False
        except Exception as e:
            LOG.warning(
                'Error trying to get zone action. Error=%(error)s',
                {
                    'error': str(e),
                }
            )

        return True

    def __call__(self):
        raise NotImplementedError
