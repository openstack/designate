# Copyright 2014 Rackspace Inc.
#
# Author: Tim Simmons <tim.simmons@rackspace.com>
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

"""
    agent.service
    ~~~~~~~~~~~~~
    Typically runs on the resolver hosts. Listen for incoming DNS requests
    on a port different than 53 and execute create_zone/delete_zone on the
    backend adaptor (e.g. Bind9)

    Configured in [service:agent]
"""
import warnings

from oslo_config import cfg

from designate.agent import handler
from designate.backend import agent_backend
from designate.conf.agent import DEFAULT_AGENT_PORT
from designate import dnsmiddleware
from designate import service
from designate import utils


CONF = cfg.CONF


class Service(service.Service):
    _dns_default_port = DEFAULT_AGENT_PORT

    def __init__(self):
        super(Service, self).__init__(
            self.service_name, threads=cfg.CONF['service:agent'].threads
        )

        warnings.warn('The designate agent service is deprecated as of the '
                      'Antelope (2023.1) release and will be removed in the '
                      '"C" release.', DeprecationWarning)

        self.dns_service = service.DNSService(
            self.dns_application, self.tg,
            cfg.CONF['service:agent'].listen,
            cfg.CONF['service:agent'].tcp_backlog,
            cfg.CONF['service:agent'].tcp_recv_timeout,
        )

        backend_driver = cfg.CONF['service:agent'].backend_driver
        self.backend = agent_backend.get_backend(backend_driver, self)

    def start(self):
        super(Service, self).start()
        self.dns_service.start()
        self.backend.start()

    def stop(self, graceful=True):
        self.dns_service.stop()
        self.backend.stop()
        super(Service, self).stop(graceful)

    @property
    def service_name(self):
        return 'agent'

    @property
    @utils.cache_result
    def dns_application(self):
        # Create an instance of the RequestHandler class
        application = handler.RequestHandler()
        if cfg.CONF['service:agent'].notify_delay > 0.0:
            application = dnsmiddleware.LimitNotifyMiddleware(application)
        application = dnsmiddleware.SerializationMiddleware(application)

        return application
