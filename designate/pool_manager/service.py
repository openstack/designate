# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
import designate.pool_manager.backend_section_name as backend_section_name

from oslo.config import cfg
from oslo import messaging

from designate import backend
from designate import exceptions
from designate import service
from designate import storage
from designate.pool_manager import cache
from designate.openstack.common import log as logging
from designate.openstack.common import threadgroup


LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('storage_driver', 'designate.central', 'service:central')


class Service(service.RPCService):
    """
    Service side of the Pool Manager RPC API.

    API version history:

        1.0 - Initial version
    """
    RPC_API_VERSION = '1.0'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

        # Get a storage connection.
        storage_driver = cfg.CONF['service:central'].storage_driver
        self.storage = storage.get_storage(storage_driver)

        # Get a pool manager cache connection.
        cache_driver = cfg.CONF['service:pool_manager'].cache_driver
        self.cache = cache.get_pool_manager_cache(cache_driver)

        self.servers = []
        self.server_backend_maps = []
        sections = backend_section_name.find_server_sections()
        for section in sections:
            backend_driver = section['backend']
            server_id = section['server_id']
            server = backend.get_server_object(backend_driver, server_id)

            backend_instance = backend.get_pool_backend(
                backend_driver, server['backend_options'])
            server_backend_map = {
                'server': server,
                'backend_instance': backend_instance
            }
            self.servers.append(server)
            self.server_backend_maps.append(server_backend_map)
        self.thread_group = threadgroup.ThreadGroup()

    def start(self):

        for server_backend_map in self.server_backend_maps:
            backend_instance = server_backend_map['backend_instance']
            backend_instance.start()

        self.thread_group.add_timer(
            cfg.CONF['service:pool_manager'].periodic_sync_interval,
            self.periodic_sync)

        super(Service, self).start()

    def stop(self):
        super(Service, self).stop()

        self.thread_group.stop(True)

        for server_backend_map in self.server_backend_maps:
            backend_instance = server_backend_map['backend_instance']
            backend_instance.stop()

    def create_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling create_domain.")
        for server_backend_map in self.server_backend_maps:
            backend_instance = server_backend_map['backend_instance']
            try:
                backend_instance.create_domain(context, domain)
                LOG.debug("success")
            except exceptions.Backend:
                LOG.debug("failure")

    def delete_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling delete_domain.")
        for server_backend_map in self.server_backend_maps:
            backend_instance = server_backend_map['backend_instance']
            try:
                backend_instance.delete_domain(context, domain)
                LOG.debug("success")
            except exceptions.Backend:
                LOG.debug("failure")

    def update_domain(self, context, domain):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :return: None
        """
        LOG.debug("Calling update_domain.")

    def update_status(self, context, domain, server, status, serial_number):
        """
        :param context: Security context information.
        :param domain: The designate domain object.
        :param server: The name server for which this serial number is
                       applicable.
        :param status: The status, 'SUCCESS' or 'ERROR'.
        :param serial_number: The serial number received from the name server
        for the domain.
        :return: None
        """
        LOG.debug("Calling update_status.")

    def periodic_sync(self):
        """
        :return: None
        """
        LOG.debug("Calling periodic_sync.")
