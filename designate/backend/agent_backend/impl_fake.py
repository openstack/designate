# Copyright 2014 Rackspace Inc.
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
# under the License.
import warnings

from oslo_log import log as logging

from designate.backend.agent_backend import base

LOG = logging.getLogger(__name__)


class FakeBackend(base.AgentBackend):
    __plugin_name__ = 'fake'

    def __init__(self, agent_service):
        super(FakeBackend, self).__init__(agent_service)
        warning_msg = ('The designate agent framework and backend driver "{}" '
                       'are deprecated as of the Antelope (2023.1) release '
                       'and will be removed in the "C" '
                       'release.'.format(self.__plugin_name__))
        warnings.warn(warning_msg, DeprecationWarning)

    def start(self):
        LOG.info("Started fake backend, Pool Manager will not work!")

    def stop(self):
        LOG.info("Stopped fake backend")

    def find_zone_serial(self, zone_name):
        LOG.debug("Finding %s", zone_name)
        return 0

    def create_zone(self, zone):
        LOG.debug("Creating %s", zone.origin.to_text())

    def update_zone(self, zone):
        LOG.debug("Updating %s", zone.origin.to_text())

    def delete_zone(self, zone_name):
        LOG.debug('Delete Zone: %s', zone_name)
