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
from neutronclient.common import exceptions as neutron_exceptions
from neutronclient.v2_0 import client as clientv20
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate.network_api import base

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_client(context, endpoint):
    params = {
        'endpoint_url': endpoint,
        'timeout': CONF['network_api:neutron'].timeout,
        'insecure': CONF['network_api:neutron'].insecure,
        'ca_cert': CONF['network_api:neutron'].ca_certificates_file,
    }

    if context.auth_token:
        params['token'] = context.auth_token
        params['auth_strategy'] = None
    elif CONF['network_api:neutron'].admin_username is not None:
        params['username'] = CONF['network_api:neutron'].admin_username
        params['project_name'] = CONF['network_api:neutron'].admin_tenant_name
        params['password'] = CONF['network_api:neutron'].admin_password
        params['auth_url'] = CONF['network_api:neutron'].auth_url
        params['auth_strategy'] = CONF['network_api:neutron'].auth_strategy
    return clientv20.Client(**params)


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
            fips = client.list_floatingips(project_id=project_id)
            for fip in fips['floatingips']:
                yield {
                    'id': fip['id'],
                    'address': fip['floating_ip_address'],
                    'region': region
                }
        except neutron_exceptions.Unauthorized:
            LOG.warning(
                'Failed fetching floating ips from %(region)s @ %(endpoint)s'
                'due to an Unauthorized error',
                {'region': region, 'endpoint': endpoint}
            )
        except Exception:
            LOG.error(
                'Failed fetching floating ips from %(region)s @ %(endpoint)s',
                {'region': region, 'endpoint': endpoint}
            )
            raise
        return
