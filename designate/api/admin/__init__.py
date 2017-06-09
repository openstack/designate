# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import pecan.deploy
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


def factory(global_config, **local_conf):
    if not cfg.CONF['service:api'].enable_api_admin:
        def disabled_app(environ, start_response):
            status = '404 Not Found'
            start_response(status, [])
            return []

        return disabled_app

    conf = {
        'app': {
            'root': 'designate.api.admin.controllers.root.RootController',
            'modules': ['designate.api.admin'],
            'errors': {
                404: '/errors/not_found',
                405: '/errors/method_not_allowed',
                '__force_dict__': True
            }
        }
    }

    app = pecan.deploy.deploy(conf)

    return app
