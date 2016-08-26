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
import abc

from designate.plugin import DriverPlugin


class AgentBackend(DriverPlugin):
    """Base class for backend implementations"""
    __plugin_type__ = 'backend'
    __plugin_ns__ = 'designate.backend.agent_backend'

    def __init__(self, agent_service):
        super(AgentBackend, self).__init__()
        self.agent_service = agent_service

    def start(self):
        pass

    def stop(self):
        pass

    @abc.abstractmethod
    def find_zone_serial(self, zone_name):
        """Find a DNS Zone"""

    @abc.abstractmethod
    def create_zone(self, zone):
        """Create a DNS zone"""
        """Zone is a DNSPython Zone object"""

    @abc.abstractmethod
    def update_zone(self, zone):
        """Update a DNS zone"""
        """Zone is a DNSPython Zone object"""

    @abc.abstractmethod
    def delete_zone(self, zone_name):
        """Delete a DNS zone"""
