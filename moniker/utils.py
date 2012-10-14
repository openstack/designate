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
from moniker.openstack.common import cfg
from moniker.openstack.common.notifier import api as notifier_api
from moniker import exceptions


def notify(context, service, event_type, payload):
    priority = 'INFO'
    publisher_id = notifier_api.publisher_id(service)

    notifier_api.notify(context, publisher_id, event_type, priority, payload)


def find_config(config_path):
    """ Find a configuration file using the given hint.

    Code nabbed from cinder.

    :param config_path: Full or relative path to the config.
    :returns: Full path of the config, if it exists.
    :raises: `moniker.exceptions.ConfigNotFound`

    """
    possible_locations = [
        config_path,
        os.path.join("etc", "moniker", config_path),
        os.path.join("etc", config_path),
        os.path.join(cfg.CONF.state_path, "etc", "moniker", config_path),
        os.path.join(cfg.CONF.state_path, "etc", config_path),
        os.path.join(cfg.CONF.state_path, config_path),
        "/etc/moniker/%s" % config_path,
    ]

    for path in possible_locations:
        if os.path.exists(path):
            return os.path.abspath(path)

    raise exceptions.ConfigNotFound(os.path.abspath(config_path))
