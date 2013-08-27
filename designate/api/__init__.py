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
import flask
from oslo.config import cfg
from designate.openstack.common import jsonutils as json

cfg.CONF.register_group(cfg.OptGroup(
    name='service:api', title="Configuration for API Service"
))

cfg.CONF.register_opts([
    cfg.IntOpt('workers', default=None,
               help='Number of worker processes to spawn'),
    cfg.StrOpt('api-base-uri', default='http://127.0.0.1:9001/'),
    cfg.StrOpt('api_host', default='0.0.0.0',
               help='API Host'),
    cfg.IntOpt('api_port', default=9001,
               help='API Port Number'),
    cfg.StrOpt('api_paste_config', default='api-paste.ini',
               help='File name for the paste.deploy config for designate-api'),
    cfg.StrOpt('auth_strategy', default='noauth',
               help='The strategy to use for auth. Supports noauth or '
                    'keystone'),
    cfg.BoolOpt('enable-api-v1', default=True),
    cfg.BoolOpt('enable-api-v2', default=False),
], group='service:api')


# Allows us to serialize datetime's etc
flask.helpers.json = json
