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

from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class Plugin(object):
    __metaclass__ = abc.ABCMeta

    __plugin_ns__ = None

    __plugin_name__ = None
    __plugin_type__ = None

    def __init__(self):
        self.name = self.get_canonical_name()
        LOG.debug("Loaded plugin %s", self.name)

    def is_enabled(self):
        """
        Is this Plugin enabled?

        :retval: Boolean
        """
        return True

    @classmethod
    def get_plugin(cls, name, ns=None, invoke_on_load=False,
                   invoke_args=(), invoke_kwds={}):
        """
        Load a plugin from namespace
        """
        ns = ns or cls.__plugin_ns__
        if ns is None:
            raise RuntimeError('No namespace provided or __plugin_ns__ unset')

        LOG.debug('Looking for plugin %s in %s', name, ns)
        mgr = driver.DriverManager(ns, name)
        mgr.driver.register_opts()

        return mgr.driver(*invoke_args, **invoke_kwds) if invoke_on_load \
            else mgr.driver

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
    def register_group_opts(cls, group_name=None, opts=None):
        """
        Register a set of Options underneath a new Group or Section
        if you will.

        :param group_name: Optional group name to register this under
                           Default: ClassName to class_name
        :param opts: The options to register.
        """
        group_name = group_name or cls.get_canonical_name()
        if not group_name:
            raise RuntimeError("Missing name")

        # NOTE(zykes): Always register the group if not the init fails...
        group = cfg.OptGroup(
            name=group_name,
            title="Configuration for %s" % group_name)
        cfg.CONF.register_group(group)
        if opts:
            cfg.CONF.register_opts(opts, group=group)
        else:
            LOG.debug("No options for %s, skipping registration", group_name)

    @classmethod
    def register_opts(cls):
        """
        Register the options for this Plugin using the options from
        cls.get_opts() as a default
        """
        opts = cls.get_opts()
        cls.register_group_opts(opts=opts)

    @classmethod
    def get_opts(cls):
        """
        Return a list of options for this plugin to be registered underneath
        it's section
        """
        return []

    def start(self):
        """
        Start this plugin
        """

    def stop(self):
        """
        Stop this plugin from doing anything
        """
