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
#
# Copied: designate

import sys
import traceback

import eventlet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr
from oslo_reports import opts as gmr_opts
from stevedore.extension import ExtensionManager

import designate.conf
from designate import utils
from designate import version

eventlet.monkey_patch(os=False)
# Monkey patch the original current_thread to use the up-to-date _active
# global variable. See https://bugs.launchpad.net/bugs/1863021 and
# https://github.com/eventlet/eventlet/issues/592
import __original_module_threading as orig_threading  # noqa
import threading  # noqa
orig_threading.current_thread.__globals__['_active'] = threading._active

CONF = designate.conf.CONF


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
    return {e.name: e.plugin for e in em.extensions}


def add_command_parsers(subparsers):
    for category, cls in get_available_commands().items():
        command_object = cls()

        parser = subparsers.add_parser(category)
        parser.set_defaults(command_object=command_object)

        category_subparsers = parser.add_subparsers(dest='action')
        category_subparsers.required = True

        for action, action_fn in methods_of(command_object):
            action = getattr(action_fn, '_cmd_name', action)
            parser = category_subparsers.add_parser(action)

            action_kwargs = []
            for args, kwargs in getattr(action_fn, 'args', []):
                parser.add_argument(*args, **kwargs)

            parser.set_defaults(action_fn=action_fn)
            parser.set_defaults(action_kwargs=action_kwargs)


category_opt = cfg.SubCommandOpt('category', title='Commands',
                                 help='Available Commands',
                                 handler=add_command_parsers)


def get_arg_string(args):
    arg = None
    if args[0] == '-':
        # (Note)zhiteng: args starts with FLAGS.oparser.prefix_chars
        # is optional args. Notice that cfg module takes care of
        # actual ArgParser so prefix_chars is always '-'.
        if args[1] == '-':
            # This is long optional arg
            arg = args[2:]
        else:
            arg = args[1:]
    else:
        arg = args

    return arg.replace('-', '_')


def fetch_func_args(func):
    fn_args = []
    for args, kwargs in getattr(func, 'args', []):
        arg = kwargs.get('dest', get_arg_string(args[0]))
        fn_args.append(getattr(CONF.category, arg))

    return fn_args


def main():
    CONF.register_cli_opt(category_opt)
    utils.read_config('designate', sys.argv)
    logging.setup(CONF, 'designate')

    gmr_opts.set_defaults(CONF)
    gmr.TextGuruMeditation.setup_autorun(version, conf=CONF)

    try:
        fn = CONF.category.action_fn
        fn_args = fetch_func_args(fn)
        fn(*fn_args)
    except Exception:
        print('An error has occurred:\n%s' % traceback.format_exc())
        return 255
