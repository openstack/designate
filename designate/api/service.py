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
from oslo_config import cfg
from oslo_log import log as logging
from paste import deploy

from designate.i18n import _LI
from designate import exceptions
from designate import utils
from designate import service
from designate import service_status


LOG = logging.getLogger(__name__)


class Service(service.WSGIService, service.Service):
    def __init__(self, threads=None):
        super(Service, self).__init__(threads=threads)

        emitter_cls = service_status.HeartBeatEmitter.get_driver(
            cfg.CONF.heartbeat_emitter.emitter_type
        )
        self.heartbeat_emitter = emitter_cls(
            self.service_name, self.tg, status_factory=self._get_status
        )

    def start(self):
        super(Service, self).start()
        self.heartbeat_emitter.start()

    def _get_status(self):
        status = "UP"
        stats = {}
        capabilities = {}
        return status, stats, capabilities

    @property
    def service_name(self):
        return 'api'

    @property
    def _wsgi_application(self):
        api_paste_config = cfg.CONF['service:api'].api_paste_config
        config_paths = utils.find_config(api_paste_config)

        if len(config_paths) == 0:
            msg = 'Unable to determine appropriate api-paste-config file'
            raise exceptions.ConfigurationError(msg)

        LOG.info(_LI('Using api-paste-config found at: %s'), config_paths[0])

        return deploy.loadapp("config:%s" % config_paths[0], name='osapi_dns')
