# Copyright 2015 Rackspace Hosting.
#
# Author: Eric Larson <eric.larson@rackspace.com>
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
import sys
import functools

import pkg_resources
from oslo_config import cfg
from oslo_log import log
from stevedore import hook


class HookLog(object):
    """Since logs are applied at import time, we record the log
    messages for later use.
    """
    LVLS = dict(
        debug=log.DEBUG,
        info=log.INFO,
        warning=log.WARNING,
        error=log.ERROR,
        critical=log.CRITICAL,
        exception=log.ERROR,
    )

    def __init__(self):
        self.messages = []

    def log(self, logger=None):
        logger = log.getLogger(__name__)
        for level, msg, args, kw in self.messages:
            logger.log(level, msg, *args, **kw)

    __call__ = log

    def capture(self, lvl, msg, *args, **kw):
        self.messages.append((lvl, msg, args, kw))

    def __getattr__(self, name):
        if name in self.LVLS:
            return functools.partial(self.capture, self.LVLS[name])

LOG = HookLog()


def log_hook_setup():
    """Replay the log messages during the hook point initialization.

    Logging isn't configured when we set up the hook points, so this
    will replay the log once the config has been loaded.
    """
    LOG()


class BaseHook(object):

    OPTS = [
        cfg.BoolOpt('disabled', default=False)
    ]

    def __init__(self, group):
        self.group = group

    @property
    def disabled(self):
        return cfg.CONF[self.group].get('disabled', False)

    def wrapper(self, *args, **kw):
        return self.hook_target(*args, **kw)

    def __call__(self, f):
        # Save our hook target as an attribute for our wrapper method
        self.hook_target = f

        @functools.wraps(self.hook_target)
        def wrapper(*args, **kw):
            if self.disabled:
                return self.hook_target(*args, **kw)
            return self.hook(*args, **kw)
        return wrapper


class hook_point(object):
    NAMESPACE = 'designate.hook_point'
    LOG_LEVEL = log.INFO

    def __init__(self, name=None):
        self._name = name
        self.log = []

    def update_config_opts(self, group, hooks):
        hooks_found = False
        for hook_impl in hooks:
            hooks_found = True

            # Add any options defined by the hook
            if hasattr(hook_impl.plugin, 'OPTS'):
                cfg.CONF.register_opts(hook_impl.plugin.OPTS, group=group)

        if not hooks_found:
            LOG.debug('No hooks found for %s', group)
        else:
            LOG.debug('Created hook: %s', group)

    def hook_manager(self, name):
        LOG.debug('Looking for hooks with: %s %s', self.NAMESPACE, name)
        return hook.HookManager(self.NAMESPACE, name)

    def find_name(self, func=None):
        """Derive the hook target path from the function name, unless
        a name has been passed in with the constructor.
        """
        if self._name:
            return self._name

        if not func:
            return None

        # derive the name from the function
        self._name = '%s.%s' % (func.__module__, func.__name__)
        return self._name

    def init_hook(self, f):
        """Set up our hook

        Try to inspect the function for a hook target path if one
        wasn't passed in and set up the necessary config options.
        """
        LOG.debug('Initializing hook: %s', f)
        self.name = self.find_name(f)
        self.group = 'hook_point:%s' % self.name
        self.hooks = self.hook_manager(self.name)
        self.update_config_opts(self.group, self.hooks)

    def enable_hook(self, ext, f):
        """Enable the hook.

        This instantiates the hook object and decorates the original
        function.
        """
        decorator = ext.plugin(self.group)
        f = decorator(f)
        f._hook_point = self  # add ourselves for inspection
        return f

    def __call__(self, f):
        # Set up all our hook information based on the function or
        # hook point
        self.init_hook(f)

        for h in self.hooks:
            f = self.enable_hook(h, f)
        return f


if __name__ == '__main__':
    # Use this script to find existing hook points.
    hook_names = sys.argv[1:]

    print('Using namespace: %s' % hook_point.NAMESPACE)

    print('pkg_resources has the following entry points:')
    for ep in pkg_resources.iter_entry_points(hook_point.NAMESPACE):
        print(ep)

    print()
    print('stevedore found the following hooks:')
    for name in hook_names:
        for hp in hook.HookManager(hook_point.NAMESPACE, name):
            print(hp)
