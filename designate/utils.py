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
import functools
import importlib.resources
import inspect
import os
import socket
import sys

from jinja2 import Template
from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils
from oslo_utils.netutils import is_valid_ipv6
from oslo_utils import uuidutils

from designate.common import config
import designate.conf
from designate import exceptions
from designate.i18n import _

LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF

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
        os.path.join(CONF.pybasedir, "etc", "designate", config_path),
        os.path.join(CONF.pybasedir, "etc", config_path),
        os.path.join(CONF.pybasedir, config_path),
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
    logging.register_options(CONF)
    config_files = find_config('%s.conf' % prog)
    cfg.CONF(argv[1:], project='designate', prog=prog,
             default_config_files=config_files)
    config.set_defaults()


def resource_string(*args):
    if len(args) == 0:
        raise ValueError()

    resource_path = importlib.resources.files(
        'designate').joinpath('resources', *args)

    if not resource_path.exists():
        raise exceptions.ResourceNotFound('Could not find the requested '
                                          'resource: %s' % resource_path)

    return resource_path.read_bytes()


def load_schema(version, name):
    schema_string = resource_string('schemas', version, '%s.json' % name)

    return jsonutils.loads(schema_string.decode('utf-8'))


def load_template(template_name):
    template_string = resource_string('templates', template_name)

    return Template(template_string.decode('utf-8'),
                    keep_trailing_newline=True)


def render_template(template, **template_context):
    if not isinstance(template, Template):
        template = load_template(template)

    return template.render(**template_context)


def execute(*cmd, **kw):
    """Execute a command in a subprocess, blocking.
    """
    root_helper = kw.pop('root_helper', CONF.root_helper)
    run_as_root = kw.pop('run_as_root', True)
    return processutils.execute(*cmd, run_as_root=run_as_root,
                                root_helper=root_helper, **kw)


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
            arg_spec = inspect.getfullargspec(f).args

            # Ensure that we have the exact number of parameters that the
            # function expects.  This handles URLs like
            # /v2/zones/<UUID - valid or invalid>/invalid
            # get, patch and delete return a 404, but Pecan returns a 405
            # for a POST at the same URL
            if len(arg_spec) != len(args):
                raise exceptions.NotFound()

            # Ensure that we have non-empty parameters in the cases where we
            # have sub controllers - i.e. controllers at the 2nd level
            # This is for URLs like /v2/zones/nameservers
            # Ideally Pecan should be handling these cases, but until then
            # we handle those cases here.
            if len(args) <= len(check):
                raise exceptions.NotFound()

            for name in check:
                pos = arg_spec.index(name)
                if not uuidutils.is_uuid_like(args[pos]):
                    raise exceptions.InvalidUUID(
                        f'Invalid UUID {name}: {args[pos]}'
                    )
            return f(*args, **kwargs)
        return functools.wraps(f)(wrapper)
    return inner


def get_proxies():
    """Return a requests compatible dict like seen here
    http://docs.python-requests.org/en/latest/user/advanced/#proxies for
    consumption in clients when we need to proxy requests.
    """
    proxies = {}
    if CONF.proxy.no_proxy:
        proxies['no_proxy'] = CONF.proxy.no_proxy
    if CONF.proxy.http_proxy is not None:
        proxies['http'] = CONF.proxy.http_proxy

    if CONF.proxy.https_proxy is not None:
        proxies['https'] = CONF.proxy.https_proxy
    elif 'http' in proxies:
        proxies['https'] = proxies['http']

    return proxies


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
    limit = params.pop('limit', CONF['service:api'].default_limit_v2)
    sort_key = params.pop('sort_key', None)
    sort_dir = params.pop('sort_dir', None)
    max_limit = CONF['service:api'].max_limit_v2

    if isinstance(limit, str) and limit.lower() == "max":
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
            if int_limit <= 0 or int_limit > sys.maxsize:
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
        msg = f'sort key must be one of {sort_keys}'
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
    LOG.info('Opening TCP Listening Socket on %(host)s:%(port)d',
             {'host': host, 'port': port})
    family = socket.AF_INET6 if is_valid_ipv6(host) else socket.AF_INET
    sock_tcp = socket.socket(family, socket.SOCK_STREAM)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # NOTE: Linux supports socket.SO_REUSEPORT only in 3.9 and later releases.
    try:
        sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        LOG.info('SO_REUSEPORT not available, ignoring.')

    # This option isn't available in the OS X version of eventlet
    if tcp_keepidle and hasattr(socket, 'TCP_KEEPIDLE'):
        sock_tcp.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPIDLE,
                            tcp_keepidle)

    sock_tcp.settimeout(1)
    sock_tcp.bind((host, port))
    if port == 0:
        newport = sock_tcp.getsockname()[1]
        LOG.info('Listening on TCP port %(port)d', {'port': newport})

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
    LOG.info('Opening UDP Listening Socket on %(host)s:%(port)d',
             {'host': host, 'port': port})
    family = socket.AF_INET6 if is_valid_ipv6(host) else socket.AF_INET
    sock_udp = socket.socket(family, socket.SOCK_DGRAM)
    sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # NOTE: Linux supports socket.SO_REUSEPORT only in 3.9 and later releases.
    try:
        sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        LOG.info('SO_REUSEPORT not available, ignoring.')

    sock_udp.settimeout(1)
    sock_udp.bind((host, port))
    if port == 0:
        newport = sock_udp.getsockname()[1]
        LOG.info('Listening on UDP port %(port)d', {'port': newport})

    return sock_udp


def max_prop_time(timeout, max_retries, retry_interval, delay):
    return timeout * max_retries + max_retries * retry_interval + delay
