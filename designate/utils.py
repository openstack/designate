# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import copy
import json
import functools
import inspect
import os
import uuid

import pkg_resources
from jinja2 import Template
from oslo.config import cfg
from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_utils import timeutils

from designate import exceptions
from designate.openstack.common.report import guru_meditation_report as gmr
from designate import version as designate_version


LOG = logging.getLogger(__name__)


cfg.CONF.register_opts([
    cfg.StrOpt('root-helper',
               default='sudo designate-rootwrap /etc/designate/rootwrap.conf')
])


# Set some proxy options (Used for clients that need to communicate via a
# proxy)
cfg.CONF.register_group(cfg.OptGroup(
    name='proxy', title="Configuration for Client Proxy"
))

proxy_opts = [
    cfg.StrOpt('http_proxy', default=None,
               help='Proxy HTTP requests via this proxy.'),
    cfg.StrOpt('https_proxy', default=None,
               help='Proxy HTTPS requests via this proxy'),
    cfg.ListOpt('no_proxy', default=[],
                help='These addresses should not be proxied')
]

cfg.CONF.register_opts(proxy_opts, group='proxy')


def find_config(config_path):
    """
    Find a configuration file using the given hint.

    Code nabbed from cinder.

    :param config_path: Full or relative path to the config.
    :returns: List of config paths
    """
    possible_locations = [
        config_path,
        os.path.join(cfg.CONF.pybasedir, "etc", "designate", config_path),
        os.path.join(cfg.CONF.pybasedir, "etc", config_path),
        os.path.join(cfg.CONF.pybasedir, config_path),
        "/etc/designate/%s" % config_path,
    ]

    found_locations = []

    for path in possible_locations:
        LOG.debug('Searching for configuration at path: %s' % path)
        if os.path.exists(path):
            LOG.debug('Found configuration at path: %s' % path)
            found_locations.append(os.path.abspath(path))

    return found_locations


def read_config(prog, argv):
    logging.register_options(cfg.CONF)
    config_files = find_config('%s.conf' % prog)
    cfg.CONF(argv[1:], project='designate', prog=prog,
             default_config_files=config_files)

    register_plugin_opts()

    # Avoid circular dependency imports
    from designate import pool_manager
    pool_manager.register_dynamic_pool_options()


def register_plugin_opts():
    # Avoid circular dependency imports
    from designate import plugin

    # Register Backend Plugin Config Options
    plugin.Plugin.register_cfg_opts('designate.backend')
    plugin.Plugin.register_extra_cfg_opts('designate.backend')

    # Register Agent Backend Plugin Config Options
    plugin.Plugin.register_cfg_opts('designate.backend.agent_backend')
    plugin.Plugin.register_extra_cfg_opts('designate.backend.agent_backend')


def resource_string(*args):
    if len(args) == 0:
        raise ValueError()

    resource_path = os.path.join('resources', *args)

    if not pkg_resources.resource_exists('designate', resource_path):
        raise exceptions.ResourceNotFound('Could not find the requested '
                                          'resource: %s' % resource_path)

    return pkg_resources.resource_string('designate', resource_path)


def load_schema(version, name):
    schema_string = resource_string('schemas', version, '%s.json' % name)

    return json.loads(schema_string)


def load_template(template_name):
    template_string = resource_string('templates', template_name)

    return Template(template_string, keep_trailing_newline=True)


def render_template(template, **template_context):
    if not isinstance(template, Template):
        template = load_template(template)

    return template.render(**template_context)


def render_template_to_file(template_name, output_path, makedirs=True,
                            **template_context):
    output_folder = os.path.dirname(output_path)

    # Create the output folder tree if necessary
    if makedirs and not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Render the template
    content = render_template(template_name, **template_context)

    with open(output_path, 'w') as output_fh:
        output_fh.write(content)


def execute(*cmd, **kw):
    root_helper = kw.pop('root_helper', cfg.CONF.root_helper)
    run_as_root = kw.pop('run_as_root', True)
    return processutils.execute(*cmd, run_as_root=run_as_root,
                                root_helper=root_helper, **kw)


def get_item_properties(item, fields, mixed_case_fields=None, formatters=None):
    """Return a tuple containing the item properties.

    :param item: a single item resource (e.g. Server, Tenant, etc)
    :param fields: tuple of strings with the desired field names
    :param mixed_case_fields: tuple of field names to preserve case
    :param formatters: dictionary mapping field names to callables
        to format the values
    """
    row = []
    mixed_case_fields = mixed_case_fields or []
    formatters = formatters or {}

    for field in fields:
        if field in formatters:
            row.append(formatters[field](item))
        else:
            if field in mixed_case_fields:
                field_name = field.replace(' ', '_')
            else:
                field_name = field.lower().replace(' ', '_')
            if not hasattr(item, field_name) and \
                    (isinstance(item, dict) and field_name in item):
                data = item[field_name]
            else:
                data = getattr(item, field_name, '')
            if data is None:
                data = ''
            row.append(data)
    return tuple(row)


def get_columns(data):
    """
    Some row's might have variable count of columns, ensure that we have the
    same.

    :param data: Results in [{}, {]}]
    """
    columns = set()

    def _seen(col):
        columns.add(str(col))

    map(lambda item: map(_seen, item.keys()), data)
    return list(columns)


def increment_serial(serial=0):
    # This provides for *roughly* unix timestamp based serial numbers
    new_serial = timeutils.utcnow_ts()

    if new_serial <= serial:
        new_serial = serial + 1

    return new_serial


def quote_string(string):
    inparts = string.split(' ')
    outparts = []
    tmp = None

    for part in inparts:
        if part == '':
            continue
        elif part[0] == '"' and part[-1:] == '"' and part[-2:] != '\\"':
            # Handle Quoted Words
            outparts.append(part.strip('"'))
        elif part[0] == '"':
            # Handle Start of Quoted Sentance
            tmp = part[1:]
        elif tmp is not None and part[-1:] == '"' and part[-2:] != '\\"':
            # Handle End of Quoted Sentance
            tmp += " " + part.strip('"')
            outparts.append(tmp)
            tmp = None
        elif tmp is not None:
            # Handle Middle of Quoted Sentance
            tmp += " " + part
        else:
            # Handle Standalone words
            outparts.append(part)

    if tmp is not None:
        # Handle unclosed quoted strings
        outparts.append(tmp)

    # This looks odd, but both calls are necessary to ensure the end results
    # is always consistent.
    outparts = [o.replace('\\"', '"') for o in outparts]
    outparts = [o.replace('"', '\\"') for o in outparts]

    return '"' + '" "'.join(outparts) + '"'


def deep_dict_merge(a, b):
    if not isinstance(b, dict):
        return b

    result = copy.deepcopy(a)

    for k, v in b.iteritems():
        if k in result and isinstance(result[k], dict):
                result[k] = deep_dict_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)

    return result


def generate_uuid():
    return str(uuid.uuid4())


def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

    """
    try:
        return str(uuid.UUID(val)) == val
    except (TypeError, ValueError, AttributeError):
        return False


def validate_uuid(*check):
    """
    A wrapper to ensure that API controller methods arguments are valid UUID's.

    Usage:
    @validate_uuid('zone_id')
    def get_all(self, zone_id):
        return {}
    """
    def inner(f):
        def wrapper(*args, **kwargs):
            arg_spec = inspect.getargspec(f).args

            # Ensure that we have the exact number of parameters that the
            # function expects.  This handles URLs like
            # /v2/zones/<UUID - valid or invalid>/invalid
            # get, patch and delete return a 404, but Pecan returns a 405
            # for a POST at the same URL
            if (len(arg_spec) != len(args)):
                raise exceptions.NotFound()

            # Ensure that we have non-empty parameters in the cases where we
            # have sub controllers - i.e. controllers at the 2nd level
            # This is for URLs like /v2/zones/nameservers
            # Ideally Pecan should be handling these cases, but until then
            # we handle those cases here.
            if (len(args) <= len(check)):
                raise exceptions.NotFound()

            for name in check:
                pos = arg_spec.index(name)
                if not is_uuid_like(args[pos]):
                    msg = 'Invalid UUID %s: %s' % (name, args[pos])
                    raise exceptions.InvalidUUID(msg)
            return f(*args, **kwargs)
        return functools.wraps(f)(wrapper)
    return inner


def get_proxies():
    """Return a requests compatible dict like seen here
    http://docs.python-requests.org/en/latest/user/advanced/#proxies for
    consumption in clients when we need to proxy requests.
    """
    proxies = {}
    if cfg.CONF.proxy.no_proxy:
        proxies['no_proxy'] = cfg.CONF.proxy.no_proxy
    if cfg.CONF.proxy.http_proxy is not None:
        proxies['http'] = cfg.CONF.proxy.http_proxy

    if cfg.CONF.proxy.https_proxy is not None:
        proxies['https'] = cfg.CONF.proxy.https_proxy
    elif 'http' in proxies:
        proxies['https'] = proxies['http']

    return proxies


def extract_priority_from_data(recordset_type, record):
    priority, data = None, record['data']
    if recordset_type in ('MX', 'SRV'):
        priority, _, data = record['data'].partition(" ")
        priority = int(priority)
    return priority, data


def cache_result(function):
    """A function decorator to cache the result of the first call, every
    additional call will simply return the cached value.

    If we were python3 only, we would have used functools.lru_cache() in place
    of this. If there's a python2 backport in a lightweight library, then we
    should switch to that.
    """
    # NOTE: We're cheating a little here, by using a mutable type (a list),
    #       we're able to read and update the value from within in inline
    #       wrapper method. If we used an immutable type, the assignment
    #       would not work as we want.
    cache = [None]

    def wrapper(*args, **kwargs):
        if cache[0] is not None:
            return cache[0]
        else:
            result = function(*args, **kwargs)
            cache[0] = result
        return result
    return wrapper


def setup_gmr(log_dir=None):
    gmr.TextGuruMeditation.setup_autorun(designate_version, log_dir=log_dir)


def split_host_port(string, default_port=53):
    try:
        (host, port) = string.split(':', 1)
        port = int(port)
    except ValueError:
        host = str(string)
        port = default_port

    return (host, port)
