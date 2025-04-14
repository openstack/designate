# Copyright 2025 Red Hat
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

import threading

from keystoneauth1 import loading as ksa_loading
from openstack.connection import Connection
from openstack import exceptions as sdk_exceptions
from oslo_log import log as logging

import designate.conf
from designate import exceptions

LOG = logging.getLogger(__name__)
CONF = designate.conf.CONF


class NeutronAuth:
    neutron_client = None
    _lock = threading.Lock()

    @classmethod
    def get_neutron_client(cls) -> Connection:
        """Create neutron client object using service credentials."""
        if cls.neutron_client is not None:
            return cls.neutron_client

        with cls._lock:
            if cls.neutron_client is not None:
                return cls.neutron_client

            try:
                LOG.debug("Loading neutron authentication from config "
                         "section 'neutron'")
                auth = ksa_loading.load_auth_from_conf_options(
                    CONF, 'neutron')
                if auth is None:
                    raise exceptions.ConfigurationError(
                        "Failed to load authentication. Please ensure "
                        "auth_type is configured in the [neutron] "
                        "section"
                    )
                session = ksa_loading.load_session_from_conf_options(
                    CONF, 'neutron', auth=auth)

                conn = Connection(
                    session=session,
                    oslo_conf=CONF,
                    service_types=['network'],
                )
                cls.neutron_client = conn
                LOG.info("Successfully created neutron client")
            except Exception as e:
                LOG.exception("Failed to create neutron client: %s", e)
                raise

        return cls.neutron_client


class NeutronClient:

    @classmethod
    def get_floating_ips(cls, filters=None):
        try:
            connection = NeutronAuth.get_neutron_client()
            floating_ips = connection.list_floating_ips(
                **filters if filters else {})
            return list(floating_ips)
        except sdk_exceptions.SDKException as e:
            message = 'Error retrieving floating IPs: %s'
            LOG.exception(message, str(e))
            raise exceptions.NeutronCommunicationFailure(
                message % str(e)) from e
