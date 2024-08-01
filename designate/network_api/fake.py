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


from oslo_log import log as logging
from oslo_utils import uuidutils

from designate.network_api import base


LOG = logging.getLogger(__name__)
POOL = {uuidutils.generate_uuid(): '192.0.2.%s' % i for i in range(1, 254)}
ALLOCATIONS = {}


def _format_floatingip(id_, address):
    return {
        'region': 'RegionOne',
        'address': address,
        'id': id_
    }


def allocate_floatingip(project_id, floatingip_id=None):
    """
    Allocates a floating ip from the pool to the project.
    """
    ALLOCATIONS.setdefault(project_id, {})

    id_ = floatingip_id or list(POOL.keys())[0]

    ALLOCATIONS[project_id][id_] = POOL.pop(id_)
    values = _format_floatingip(id_, ALLOCATIONS[project_id][id_])
    LOG.debug('Allocated to id_ %s to %s - %s', id_, project_id, values)
    return values


def deallocate_floatingip(id_):
    """
    Deallocate a floatingip
    """
    LOG.debug('De-allocating %s', id_)
    for project_id, allocated in list(ALLOCATIONS.items()):
        if id_ in allocated:
            POOL[id_] = allocated.pop(id_)
            break


def reset_floatingips():
    LOG.debug('Resetting any allocations.')
    for project_id, allocated in list(ALLOCATIONS.items()):
        for key, value in list(allocated.items()):
            POOL[key] = allocated.pop(key)


class FakeNetworkAPI(base.NetworkAPI):
    __plugin_name__ = 'fake'

    def list_floatingips(self, context, region=None):
        if context.is_admin:
            data = []
            for project_id, allocated in list(ALLOCATIONS.items()):
                data.extend(list(allocated.items()))
        else:
            data = list(ALLOCATIONS.get(context.project_id, {}).items())

        formatted = [_format_floatingip(k, v) for k, v in data]
        LOG.debug(
            'Returning %i FloatingIPs: %s', len(formatted), formatted
        )
        return formatted
