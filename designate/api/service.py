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

# NOTE: This module provides WSGIService which uses oslo_service.wsgi and
# oslo_service.sslutils. These modules will be removed in oslo.service 2026.2
# as they are built on eventlet. WSGIService and the designate-api service are
# deprecated. Deploy Designate API via uwsgi instead. See the DevStack
# configuration for an example of uwsgi deployment.

from debtcollector import removals
from oslo_log import log as logging
from oslo_utils import netutils
from paste import deploy

import designate.conf
from designate import exceptions
from designate import service
from designate import utils


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)

removals.removed_module(
    __name__,
    removal_version="2027.1",
    message=(
        "The designate.api.service module is deprecated. WSGIService uses "
        "oslo_service.wsgi and oslo_service.sslutils which will be removed "
        "in oslo.service 2026.2. Deploy Designate API via uwsgi instead. "
        "See the DevStack configuration for an example of uwsgi deployment."
    ),
)


class WSGIService(service.Service):
    def __init__(self, app, name, listen, max_url_len=None):
        from oslo_service import sslutils
        from oslo_service import wsgi

        super().__init__(name)
        self.app = app
        self.name = name

        self.listen = listen

        self.servers = []

        for address in self.listen:
            host, port = netutils.parse_host_port(address)
            server = wsgi.Server(
                CONF, name, app,
                host=host,
                port=port,
                pool_size=CONF['service:api'].threads,
                backlog=CONF.backlog,
                use_ssl=sslutils.is_enabled(CONF),
                max_url_len=max_url_len
            )

            self.servers.append(server)

    def start(self):
        for server in self.servers:
            server.start()
        super().start()

    def stop(self, graceful=True):
        for server in self.servers:
            server.stop()
        super().stop(graceful)

    def wait(self):
        for server in self.servers:
            server.wait()
        super().wait()


class Service(WSGIService):
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
