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
import os
import pkg_resources
import json
from jinja2 import Template
from designate.openstack.common import log as logging
from oslo.config import cfg
from designate.openstack.common import processutils
from designate.openstack.common import timeutils
from designate import exceptions

LOG = logging.getLogger(__name__)


cfg.CONF.register_opts([
    cfg.StrOpt('root-helper',
               default='sudo designate-rootwrap /etc/designate/rootwrap.conf')
])


def find_config(config_path):
    """
    Find a configuration file using the given hint.

    Code nabbed from cinder.

    :param config_path: Full or relative path to the config.
    :returns: List of config paths
    """
    possible_locations = [
        config_path,
        os.path.join(cfg.CONF.state_path, "etc", "designate", config_path),
        os.path.join(cfg.CONF.state_path, "etc", config_path),
        os.path.join(cfg.CONF.state_path, config_path),
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
    config_files = find_config('%s.conf' % prog)

    cfg.CONF(argv[1:], project='designate', prog=prog,
             default_config_files=config_files)


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

    return Template(template_string)


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


def get_item_properties(item, fields, mixed_case_fields=[], formatters={}):
    """Return a tuple containing the item properties.

    :param item: a single item resource (e.g. Server, Tenant, etc)
    :param fields: tuple of strings with the desired field names
    :param mixed_case_fields: tuple of field names to preserve case
    :param formatters: dictionary mapping field names to callables
        to format the values
    """
    row = []

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
