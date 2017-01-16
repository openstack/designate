# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
import six
from oslo_log import log as logging

from designate.utils import generate_uuid
from designate.network_api import base


LOG = logging.getLogger(__name__)

POOL = dict([(generate_uuid(), '192.168.2.%s' % i) for i in
             range(0, 254)])
ALLOCATIONS = {}


def _format_floatingip(id_, address):
    return {
        'region': u'RegionOne',
        'address': address,
        'id': id_
    }


def allocate_floatingip(tenant_id, floatingip_id=None):
    """
    Allocates a floating ip from the pool to the tenant.
    """
    ALLOCATIONS.setdefault(tenant_id, {})

    id_ = floatingip_id or list(six.iterkeys(POOL))[0]

    ALLOCATIONS[tenant_id][id_] = POOL.pop(id_)
    values = _format_floatingip(id_, ALLOCATIONS[tenant_id][id_])
    LOG.debug("Allocated to id_ %s to %s - %s", id_, tenant_id, values)
    return values


def deallocate_floatingip(id_):
    """
    Deallocate a floatingip
    """
    LOG.debug('De-allocating %s', id_)
    for tenant_id, allocated in list(ALLOCATIONS.items()):
        if id_ in allocated:
            POOL[id_] = allocated.pop(id_)
            break
    else:
        raise KeyError('No such FloatingIP %s' % id_)


def reset_floatingips():
    LOG.debug('Resetting any allocations.')
    for tenant_id, allocated in list(ALLOCATIONS.items()):
        for key, value in list(allocated.items()):
            POOL[key] = allocated.pop(key)


class FakeNetworkAPI(base.NetworkAPI):
    __plugin_name__ = 'fake'

    def list_floatingips(self, context, region=None):
        if context.is_admin:
            data = []
            for tenant_id, allocated in list(ALLOCATIONS.items()):
                data.extend(list(allocated.items()))
        else:
            data = list(ALLOCATIONS.get(context.tenant, {}).items())

        formatted = [_format_floatingip(k, v) for k, v in data]
        LOG.debug('Returning %i FloatingIPs: %s',
                  len(formatted), formatted)
        return formatted
