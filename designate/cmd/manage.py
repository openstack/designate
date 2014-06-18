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
import sys

from oslo.config import cfg
from stevedore.extension import ExtensionManager

from designate.openstack.common import log as logging
from designate.openstack.common import strutils
from designate import utils


def methods_of(obj):
    """Get all callable methods of an object that don't start with underscore

    returns a list of tuples of the form (method_name, method)
    """
    result = []
    for i in dir(obj):
        if callable(getattr(obj, i)) and not i.startswith('_'):
            result.append((i, getattr(obj, i)))
    return result


def get_available_commands():
    em = ExtensionManager('designate.manage')
    return dict([(e.name, e.plugin) for e in em.extensions])


def add_command_parser(subparsers):
    # for name, category in get_available_commands()
    # parser = subparsers.add_parser('db')
    for name, cls in get_available_commands().items():
        obj = cls()

        # A Category like 'database' etc
        parser = subparsers.add_parser(name)
        parser.set_defaults(command_object=obj)

        category_subparsers = parser.add_subparsers(dest=name)

        for (action, action_fn) in methods_of(obj):
            action_name = getattr(action_fn, '_cmd_name', action)
            cmd_parser = category_subparsers.add_parser(action_name)

            action_kwargs = []
            for args, kwargs in getattr(action_fn, 'args', []):
                kwargs.setdefault('dest', args[0][2:])
                if kwargs['dest'].startswith('action_kwarg_'):
                    action_kwargs.append(
                        kwargs['dest'][len('action_kwarg_'):])
                else:
                    action_kwargs.append(kwargs['dest'])
                    kwargs['dest'] = 'action_kwarg_' + kwargs['dest']
                cmd_parser.add_argument(*args, **kwargs)

            cmd_parser.set_defaults(action_fn=action_fn)
            cmd_parser.set_defaults(action_kwargs=action_kwargs)

            cmd_parser.add_argument('action_args', nargs='*')


command_opt = cfg.SubCommandOpt('command', title="Commands",
                                help="Available Commands",
                                handler=add_command_parser)


def main():
    cfg.CONF.register_cli_opt(command_opt)

    utils.read_config('designate', sys.argv)
    logging.setup('designate')

    func_kwargs = {}
    for k in cfg.CONF.command.action_kwargs:
        v = getattr(cfg.CONF.command, 'action_kwarg_' + k)
        if v is None:
            continue
        func_kwargs[k] = strutils.safe_decode(v)
    func_args = [strutils.safe_decode(arg)
                 for arg in cfg.CONF.command.action_args]
    return cfg.CONF.command.action_fn(*func_args, **func_kwargs)
