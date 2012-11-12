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
import os
import pkg_resources
from jinja2 import Template
from moniker.openstack.common import log as logging
from moniker.openstack.common import cfg
from moniker.openstack.common.notifier import api as notifier_api
from moniker import exceptions

LOG = logging.getLogger(__name__)


def notify(context, service, event_type, payload):
    priority = 'INFO'
    publisher_id = notifier_api.publisher_id(service)

    notifier_api.notify(context, publisher_id, event_type, priority, payload)


def find_config(config_path):
    """
    Find a configuration file using the given hint.

    Code nabbed from cinder.

    :param config_path: Full or relative path to the config.
    :returns: Full path of the config, if it exists.
    :raises: `moniker.exceptions.ConfigNotFound`
    """
    possible_locations = [
        config_path,
        os.path.join(cfg.CONF.state_path, "etc", "moniker", config_path),
        os.path.join(cfg.CONF.state_path, "etc", config_path),
        os.path.join(cfg.CONF.state_path, config_path),
        "/etc/moniker/%s" % config_path,
    ]

    for path in possible_locations:
        LOG.debug('Searching for configuration at path: %s' % path)
        if os.path.exists(path):
            LOG.debug('Found configuration at path: %s' % path)
            return os.path.abspath(path)

    msg = 'No configuration file found for %s' % config_path
    raise exceptions.ConfigNotFound(msg)


def read_config(prog, argv=None):
    config_files = [find_config('%s.conf' % prog)]

    cfg.CONF(argv, project='moniker', prog=prog,
             default_config_files=config_files)


def resource_string(*args):
    if len(args) == 0:
        raise ValueError()

    resource_path = os.path.join('resources', *args)

    if not pkg_resources.resource_exists('moniker', resource_path):
        raise exceptions.ResourceNotFound('Could not find the requested '
                                          'resource: %s' % resource_path)

    return pkg_resources.resource_string('moniker', resource_path)


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
