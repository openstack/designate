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

from neutronclient.v2_0 import client as clientv20
from neutronclient.common import exceptions as neutron_exceptions
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import threadgroup

from designate import exceptions
from designate.i18n import _LW
from designate.i18n import _LE
from designate.network_api import base


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


neutron_group = cfg.OptGroup(
            name='network_api:neutron', title="Configuration network api"
        )

neutron_opts = [
    cfg.ListOpt('endpoints',
                help='URL to use if None in the ServiceCatalog that is '
                'passed by the request context. Format: <region>|<url>'),
    cfg.StrOpt('endpoint_type', default='publicURL',
               help="Endpoint type to use"),
    cfg.IntOpt('timeout',
               default=30,
               help='timeout value for connecting to neutron in seconds'),
    cfg.StrOpt('admin_username',
               help='username for connecting to neutron in admin context'),
    cfg.StrOpt('admin_password',
               help='password for connecting to neutron in admin context',
               secret=True),
    cfg.StrOpt('admin_tenant_name',
               help='tenant name for connecting to neutron in admin context'),
    cfg.StrOpt('auth_url',
               help='auth url for connecting to neutron in admin context'),
    cfg.BoolOpt('insecure',
                default=False,
                help='if set, ignore any SSL validation issues'),
    cfg.StrOpt('auth_strategy',
               default='keystone',
               help='auth strategy for connecting to '
                    'neutron in admin context'),
    cfg.StrOpt('ca_certificates_file',
               help='Location of ca certificates file to use for '
                    'neutron client requests.'),
]

cfg.CONF.register_group(neutron_group)
cfg.CONF.register_opts(neutron_opts, group=neutron_group)


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
        params['tenant_name'] = CONF['network_api:neutron'].admin_tenant_name
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
            region=region)

        tg = threadgroup.ThreadGroup()

        failed = []
        data = []

        def _call(endpoint, region, *args, **kw):
            client = get_client(context, endpoint=endpoint)
            LOG.debug("Attempting to fetch FloatingIPs from %s @ %s",
                      endpoint, region)
            try:
                fips = client.list_floatingips(*args, **kw)
            except neutron_exceptions.Unauthorized as e:
                # NOTE: 401 might be that the user doesn't have neutron
                # activated in a particular region, we'll just log the failure
                # and go on with our lives.
                LOG.warning(_LW("Calling Neutron resulted in a 401, "
                                "please investigate."))
                LOG.exception(e)
                return
            except Exception as e:
                LOG.error(_LE('Failed calling Neutron '
                              '%(region)s - %(endpoint)s'),
                          {'region': region, 'endpoint': endpoint})
                LOG.exception(e)
                failed.append((e, endpoint, region))
                return

            for fip in fips['floatingips']:
                data.append({
                    'id': fip['id'],
                    'address': fip['floating_ip_address'],
                    'region': region
                })

            LOG.debug("Added %i FloatingIPs from %s @ %s",
                      len(data), endpoint, region)

        for endpoint, region in endpoints:
            tg.add_thread(_call, endpoint, region,
                          tenant_id=context.tenant)
        tg.wait()

        # NOTE: Sadly tg code doesn't give us a good way to handle failures.
        if failed:
            msg = 'Failed retrieving FloatingIPs from Neutron in %s' % \
                ", ".join(['%s - %s' % (i[1], i[2]) for i in failed])
            raise exceptions.NeutronCommunicationFailure(msg)
        return data
