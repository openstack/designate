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
from oslo_log import log as logging
from paste import deploy

import designate.conf
from designate import exceptions
from designate import service
from designate import utils


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class Service(service.WSGIService):
    def __init__(self):
        super().__init__(
            self.wsgi_application,
            self.service_name,
            CONF['service:api'].listen,
        )

    def start(self):
        super().start()

    def stop(self, graceful=True):
        super().stop(graceful)

    @property
    def service_name(self):
        return 'api'

    @property
    def wsgi_application(self):
        api_paste_config = CONF['service:api'].api_paste_config
        config_paths = utils.find_config(api_paste_config)

        if not config_paths:
            raise exceptions.ConfigurationError(
                'Unable to determine appropriate api-paste-config file'
            )

        LOG.info('Using api-paste-config found at: %s', config_paths[0])

        return deploy.loadapp("config:%s" % config_paths[0], name='osapi_dns')
