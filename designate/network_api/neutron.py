# Copyright 2012 OpenStack Foundation
# All Rights Reserved
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
#
# Copied partially from nova
import concurrent.futures
import futurist
from keystoneauth1 import session
from keystoneauth1 import token_endpoint
import openstack
from openstack import exceptions as sdk_exceptions
from oslo_log import log as logging

import designate.conf
from designate import exceptions
from designate.network_api import base
from designate import version


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


def get_client(context, endpoint):
    verify = True
    if CONF['network_api:neutron'].insecure:
        verify = False
    elif CONF['network_api:neutron'].ca_certificates_file:
        verify = CONF['network_api:neutron'].ca_certificates_file

    auth_token = token_endpoint.Token(endpoint, context.auth_token)

    user_session = session.Session(
        auth=auth_token,
        verify=verify,
        cert=CONF['network_api:neutron'].client_certificate_file,
        timeout=CONF['network_api:neutron'].timeout,
        app_name='designate',
        app_version=version.version_info.version_string())

    return openstack.connection.Connection(session=user_session)


class NeutronNetworkAPI(base.NetworkAPI):
    """
    Interact with the Neutron API
    """
    __plugin_name__ = 'neutron'

    def list_floatingips(self, context, region=None):
        """
        Get floating ips based on the current context from Neutron
        """
        endpoints = self._endpoints(
            service_catalog=context.service_catalog,
            service_type='network',
            endpoint_type=CONF['network_api:neutron'].endpoint_type,
            config_section='network_api:neutron',
            region=region
        )

        floating_ips = []
        with futurist.GreenThreadPoolExecutor(max_workers=5) as executor:
            executors = [
                executor.submit(
                    self._get_floating_ips,
                    context,
                    endpoint,
                    region,
                    project_id=context.project_id
                ) for endpoint, region in endpoints
            ]
            for future in concurrent.futures.as_completed(executors):
                try:
                    floating_ips.extend(future.result())
                except Exception as e:
                    raise exceptions.NeutronCommunicationFailure(e)

        return floating_ips

    @staticmethod
    def _get_floating_ips(context, endpoint, region, project_id):
        LOG.debug('Fetching floating ips from %(region)s @ %(endpoint)s',
                  {'region': region, 'endpoint': endpoint})
        client = get_client(context, endpoint=endpoint)
        try:
            fips = client.network.ips(project_id=project_id)
            for fip in fips:
                yield {
                    'id': fip['id'],
                    'address': fip['floating_ip_address'],
                    'region': region
                }
        except sdk_exceptions.HttpException as http_ex:
            LOG.warning(
                'Failed fetching floating ips from %(region)s @ %(endpoint)s'
                'due to a %(cause)s error',
                {'region': region,
                 'endpoint': endpoint,
                 'cause': http_ex.message}
            )
        except Exception:
            LOG.error(
                'Failed fetching floating ips from %(region)s @ %(endpoint)s',
                {'region': region, 'endpoint': endpoint}
            )
            raise
        return
