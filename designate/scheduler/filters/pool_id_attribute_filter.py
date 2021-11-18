# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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

from designate import exceptions
from designate import objects
from designate import policy
from designate.scheduler.filters import base

LOG = logging.getLogger(__name__)


class PoolIDAttributeFilter(base.Filter):
    """This allows users with the correct role to specify the exact pool_id
    to schedule the supplied zone to.

    This is supplied as an attribute on the zone

    .. code-block:: python
        :emphasize-lines: 3

        {
            "attributes": {
                "pool_id": "794ccc2c-d751-44fe-b57f-8894c9f5c842"
            },
            "email": "user@example.com",
            "name": "example.com."
        }

    The pool is loaded to ensure it exists, and then a policy check is
    performed to ensure the user has the correct role.

    .. warning::

        This should only be enabled if required, as it will raise a
        403 Forbidden if a user without the correct role uses it.
    """

    name = 'pool_id_attribute'
    """Name to enable in the ``[designate:central:scheduler].filters`` option
    list
    """

    def filter(self, context, pools, zone):
        """Attempt to load and set the pool to the one provided in the
        Zone attributes.

        :param context: :class:`designate.context.DesignateContext` - Context
            Object from request
        :param pools: :class:`designate.objects.pool.PoolList` - List of pools
            to choose from
        :param zone: :class:`designate.objects.zone.Zone` - Zone to be created
        :return: :class:`designate.objects.pool.PoolList` -- A PoolList with
            containing a single pool.
        :raises: Forbidden, PoolNotFound
        """

        try:
            if zone.attributes.get('pool_id'):
                pool_id = zone.attributes.get('pool_id')
                try:
                    pool = self.storage.get_pool(context, pool_id)
                except Exception:
                    return objects.PoolList()
                policy.check('zone_create_forced_pool', context, pool)
                if pool in pools:
                    pools = objects.PoolList()
                    pools.append(pool)
                return pools
            else:
                return pools
        except exceptions.RelationNotLoaded:
            return pools
