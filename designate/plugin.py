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

import six
from stevedore import driver
from stevedore import enabled
from stevedore import extension
from oslo_config import cfg
from oslo_log import log as logging


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


@six.add_metaclass(abc.ABCMeta)
class Plugin(object):
    __plugin_ns__ = None

    __plugin_name__ = None
    __plugin_type__ = None

    def __init__(self):
        self.name = self.get_canonical_name()
        LOG.debug("Loaded plugin %s" % self.name)

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

    @classmethod
    def get_cfg_opts(cls):
        """Get any static configuration options

        Returns an array of tuples in the form:

        [(group1, [Option1, Option2]), (group2, [Option1, Option2])]
        """
        return []

    @classmethod
    def get_extra_cfg_opts(cls):
        """Get any dynamically built configuration options

        Returns an array of tuples in the form:

        [(group1, [Option1, Option2]), (group2, [Option1, Option2])]
        """
        return []

    @classmethod
    def register_cfg_opts(cls, namespace):
        mgr = extension.ExtensionManager(namespace)

        for e in mgr:
            for group, opts in e.plugin.get_cfg_opts():
                if isinstance(group, six.string_types):
                    group = cfg.OptGroup(name=group)

                CONF.register_group(group)
                CONF.register_opts(opts, group=group)

    @classmethod
    def register_extra_cfg_opts(cls, namespace):
        mgr = extension.ExtensionManager(namespace)

        for e in mgr:
            for group, opts in e.plugin.get_extra_cfg_opts():
                if isinstance(group, six.string_types):
                    group = cfg.OptGroup(name=group)

                CONF.register_group(group)
                CONF.register_opts(opts, group=group)


class DriverPlugin(Plugin):
    """
    A Driver plugin is a singleton, where only a single driver will loaded
    at a time.

    For example: Storage implementations (SQLAlchemy)
    """

    @classmethod
    def get_driver(cls, name):
        """Load a single driver"""

        LOG.debug('Looking for driver %s in %s' % (name, cls.__plugin_ns__))

        mgr = driver.DriverManager(cls.__plugin_ns__, name)

        return mgr.driver


class ExtensionPlugin(Plugin):
    """
    Extension plugins are loaded as a group, where multiple extensions will
    be loaded and used at the same time.

    For example: Designate Sink handlers
    """

    @classmethod
    def get_extensions(cls, enabled_extensions=None):
        """Load a series of extensions"""

        LOG.debug('Looking for extensions in %s' % cls.__plugin_ns__)

        def _check_func(ext):
            if enabled_extensions is None:
                # All extensions are enabled by default, if no specific list
                # is specified
                return True

            return ext.plugin.get_plugin_name() in enabled_extensions

        mgr = enabled.EnabledExtensionManager(
            cls.__plugin_ns__, check_func=_check_func,
            propagate_map_exceptions=True)

        return [e.plugin for e in mgr]
