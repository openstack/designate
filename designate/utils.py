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
import socket

import six
import pkg_resources
from jinja2 import Template
from oslo_config import cfg
from oslo_concurrency import processutils
from oslo_log import log as logging
from oslo_utils import timeutils
from oslo_utils import uuidutils
from oslo_utils.netutils import is_valid_ipv6

from designate.common import config
from designate import exceptions
from designate.i18n import _
from designate.i18n import _LI


LOG = logging.getLogger(__name__)


helper_opts = [
    cfg.StrOpt('root-helper',
               default='sudo designate-rootwrap /etc/designate/rootwrap.conf',
               help='designate-rootwrap configuration')
]


# Set some proxy options (Used for clients that need to communicate via a
# proxy)
proxy_group = cfg.OptGroup(
    name='proxy', title="Configuration for Client Proxy"
)

proxy_opts = [
    cfg.StrOpt('http_proxy',
               help='Proxy HTTP requests via this proxy.'),
    cfg.StrOpt('https_proxy',
               help='Proxy HTTPS requests via this proxy'),
    cfg.ListOpt('no_proxy', default=[],
                help='These addresses should not be proxied')
]


cfg.CONF.register_opts(helper_opts)
cfg.CONF.register_group(proxy_group)
cfg.CONF.register_opts(proxy_opts, proxy_group)

# Default TCP/UDP ports

DEFAULT_AGENT_PORT = 5358
DEFAULT_MDNS_PORT = 5354


# Default datetime format

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


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
    config.set_defaults()

    register_plugin_opts()

    # Avoid circular dependency imports
    from designate import pool_manager
    pool_manager.register_dynamic_pool_options()


def register_plugin_opts():
    # Avoid circular dependency imports
    from designate import plugin

    # Register Producer Tasks
    plugin.Plugin.register_cfg_opts('designate.producer_tasks')
    plugin.Plugin.register_extra_cfg_opts('designate.producer_tasks')

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

    return json.loads(schema_string.decode('utf-8'))


def load_template(template_name):
    template_string = resource_string('templates', template_name)

    return Template(template_string.decode('utf-8'),
                    keep_trailing_newline=True)


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
    """Execute a command in a subprocess, blocking.
    """
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

    six.moves.map(lambda item: six.moves.map(_seen,
        list(six.iterkeys(item))), data)
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

    for k, v in b.items():
        if k in result and isinstance(result[k], dict):
                result[k] = deep_dict_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)

    return result


def generate_uuid():
    return uuidutils.generate_uuid(dashed=True)


def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

    """
    return uuidutils.is_uuid_like(val)


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
    cache = []

    def wrapper(cls_instance):
        if not cache:
            cache.append(function(cls_instance))
        return cache[0]
    return wrapper


def split_host_port(string, default_port=53):
    try:
        (host, port) = string.split(':', 1)
        port = int(port)
    except ValueError:
        host = str(string)
        port = default_port

    return (host, port)


def get_paging_params(context, params, sort_keys):
    """
    Extract any paging parameters
    """
    marker = params.pop('marker', None)
    limit = params.pop('limit', cfg.CONF['service:api'].default_limit_v2)
    sort_key = params.pop('sort_key', None)
    sort_dir = params.pop('sort_dir', None)
    max_limit = cfg.CONF['service:api'].max_limit_v2

    if isinstance(limit, six.string_types) and limit.lower() == "max":
        # Support for retrieving the max results at once. If set to "max",
        # the configured max limit will be used.
        limit = max_limit

    elif limit:
        # Negative and zero limits are not caught in storage.
        # With a number bigger than MAXSIZE, rpc throws an 'OverflowError long
        # too big to convert'.
        # So the parameter 'limit' is checked here.
        invalid_limit_message = ('limit should be an integer between 1 and '
                                 '%(max)s' % {'max': max_limit})
        try:
            int_limit = int(limit)
            if int_limit <= 0 or int_limit > six.MAXSIZE:
                raise exceptions.InvalidLimit(invalid_limit_message)
        # This exception is raised for non ints when int(limit) is called
        except ValueError:
            raise exceptions.InvalidLimit(invalid_limit_message)

    # sort_dir is checked in paginate_query.
    # We duplicate the sort_dir check here to throw a more specific
    # exception than ValueError.
    if sort_dir and sort_dir not in ['asc', 'desc']:
        raise exceptions.InvalidSortDir(_("Unknown sort direction, "
                                          "must be 'desc' or 'asc'"))

    if sort_keys is None:
        sort_key = None
        sort_dir = None

    elif sort_key and sort_key not in sort_keys:
        msg = 'sort key must be one of %(keys)s' % {'keys': sort_keys}
        raise exceptions.InvalidSortKey(msg)
    elif sort_key == 'tenant_id' and not context.all_tenants:
        sort_key = None

    return marker, limit, sort_key, sort_dir


def bind_tcp(host, port, tcp_backlog, tcp_keepidle=None):
    """Bind to a TCP port and listen.
    Use reuseaddr, reuseport if available, keepalive if specified

    :param host: IPv4/v6 address or "". "" binds to every IPv4 interface.
    :type host: str
    :param port: TCP port
    :type port: int
    :param tcp_backlog: TCP listen backlog
    :type tcp_backlog: int
    :param tcp_keepidle: TCP keepalive interval
    :type tcp_keepidle: int
    :returns: socket
    """
    LOG.info(_LI('Opening TCP Listening Socket on %(host)s:%(port)d'),
             {'host': host, 'port': port})
    family = socket.AF_INET6 if is_valid_ipv6(host) else socket.AF_INET
    sock_tcp = socket.socket(family, socket.SOCK_STREAM)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # NOTE: Linux supports socket.SO_REUSEPORT only in 3.9 and later releases.
    try:
        sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        LOG.info(_LI('SO_REUSEPORT not available, ignoring.'))

    # This option isn't available in the OS X version of eventlet
    if tcp_keepidle and hasattr(socket, 'TCP_KEEPIDLE'):
        sock_tcp.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPIDLE,
                            tcp_keepidle)

    sock_tcp.setblocking(True)
    sock_tcp.bind((host, port))
    if port == 0:
        newport = sock_tcp.getsockname()[1]
        LOG.info(_LI('Listening on TCP port %(port)d'), {'port': newport})

    sock_tcp.listen(tcp_backlog)

    return sock_tcp


def bind_udp(host, port):
    """Bind to an UDP port and listen.
    Use reuseaddr, reuseport if available

    :param host: IPv4/v6 address or "". "" binds to every IPv4 interface.
    :type host: str
    :param port: UDP port
    :type port: int
    :returns: socket
    """
    LOG.info(_LI('Opening UDP Listening Socket on %(host)s:%(port)d'),
             {'host': host, 'port': port})
    family = socket.AF_INET6 if is_valid_ipv6(host) else socket.AF_INET
    sock_udp = socket.socket(family, socket.SOCK_DGRAM)
    sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # NOTE: Linux supports socket.SO_REUSEPORT only in 3.9 and later releases.
    try:
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        LOG.info(_LI('SO_REUSEPORT not available, ignoring.'))

    sock_udp.setblocking(True)
    sock_udp.bind((host, port))
    if port == 0:
        newport = sock_udp.getsockname()[1]
        LOG.info(_LI('Listening on UDP port %(port)d'), {'port': newport})

    return sock_udp


def max_prop_time(timeout, max_retries, retry_interval, delay):
    return timeout * max_retries + max_retries * retry_interval + delay
