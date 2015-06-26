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
import six
from mock import Mock
from mock import patch
from oslo_config import cfg
from stevedore.hook import HookManager
from stevedore.extension import Extension

from designate.hookpoints import hook_point
from designate.hookpoints import BaseHook
from designate.tests import TestCase


class AddHook(BaseHook):

    OPTS = [
        cfg.Opt('bar'),
    ]

    @property
    def bar(self):
        return cfg.CONF[self.group].bar

    def hook(self, *args, **kw):
        return self.hook_target(*args, **kw) + 1


def get_hook_manager(*hooks):
    hooks = hooks or [AddHook]

    group = 'hook_point:foo'
    ext = [
        Extension('designate_hook', 'foo', hook, hook(group))
        for hook in hooks
    ]
    return HookManager.make_test_instance(ext, 'designate_hook')


def inc(num):
    return num + 1


class TestHookpoints(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        group = 'hook_point:foo'
        self.CONF.register_group(cfg.OptGroup(group))
        self.CONF.register_opts(BaseHook.OPTS, group=group)

    def test_no_hookpoint_is_noop(self):

        def doit(self, name):
            return 'done: %s' % name

        self.assertEqual(doit, hook_point('foo')(doit))

    def test_hook_is_decorator(self):
        hp = hook_point('foo')
        hp.hook_manager = Mock(return_value=get_hook_manager())
        assert hp(inc)(1) == 3

    def test_apply_N_hooks(self):
        hp = hook_point('foo')
        hp.hook_manager = Mock(return_value=get_hook_manager(AddHook, AddHook))
        assert hp(inc)(1) == 4

    def test_hook_init(self):
        hp = hook_point('foo')

        # Make sure we set up our object when the hook point is
        # applied to a function / method.
        hp.find_name = Mock(return_value='foo.bar.baz')
        hp.hook_manager = Mock(return_value=get_hook_manager())
        hp.find_config = Mock(return_value={'enabled': True})
        hp.update_config_opts = Mock()

        hp(inc)
        self.assertEqual(hp.name, 'foo.bar.baz')
        self.assertEqual(hp.group, 'hook_point:foo.bar.baz')
        hp.update_config_opts.assert_called_with(hp.group, hp.hooks)


class TestHookpointsConfigOpts(TestCase):
    """Make sure hooks add the necessary config opts.
    """

    def test_hook_adds_config_opts(self):
        hp = hook_point('foo')
        hp.hook_manager = Mock(return_value=get_hook_manager())
        hp(inc)
        assert hp.group in list(six.iterkeys(self.CONF))


class TestHookpointsEnabling(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        # NOTE: The options need to be added here via the test classes
        #       CONF in order to fall through
        group = 'hook_point:foo'
        self.CONF.register_group(cfg.OptGroup(group))
        self.CONF.register_opts(BaseHook.OPTS, group=group)

    @patch.object(hook_point, 'hook_manager',
                  Mock(return_value=get_hook_manager()))
    def test_hook_disabled(self):
        hp = hook_point('foo')
        result_func = hp(inc)

        # We should now have a config option we can set to disabled
        self.config(disabled=True, group='hook_point:foo')

        # The result is 2 so no extra add hook was applied
        self.assertEqual(result_func(1), 2)

    @patch.object(hook_point, 'hook_manager',
                  Mock(return_value=get_hook_manager()))
    def test_hook_enabled_when_config_key_exists(self):
        hp = hook_point('foo')
        hp(inc)

        # Add our config
        self.config(bar='from config', group='hook_point:foo')

        # reapply our hook
        result_func = hp(inc)

        # The result is 3 so the extra add hook was applied
        self.assertEqual(result_func(1), 3)
