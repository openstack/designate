# Copyright 2012 Bouvet ASA
#
# Author: Endre Karlson <endre.karlson@bouvet.no>
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
from stevedore import driver
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class Plugin(object):
    __metaclass__ = abc.ABCMeta

    __plugin_ns__ = None

    __plugin_name__ = None
    __plugin_type__ = None

    def __init__(self):
        self.name = self.get_canonical_name()
        LOG.debug("Loaded plugin %s", self.name)

    @classmethod
    def get_canonical_name(cls):
        """
        Return the plugin name
        """
        type_ = cls.get_plugin_type()
        name = cls.get_plugin_name()
        return "%s:%s" % (type_, name)

    @classmethod
    def get_plugin_name(cls):
        return cls.__plugin_name__

    @classmethod
    def get_plugin_type(cls):
        return cls.__plugin_type__


class DriverPlugin(Plugin):
    @classmethod
    def get_driver(cls, name):
        """ Load a driver """

        LOG.debug('Looking for driver %s in %s', name, cls.__plugin_ns__)

        mgr = driver.DriverManager(cls.__plugin_ns__, name)

        return mgr.driver
