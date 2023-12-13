# Copyright 2016 Hewlett-Packard Development Company, L.P.
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
from oslo_utils.strutils import bool_from_string

from designate import exceptions
from designate.objects import PoolList
from designate.scheduler.filters import base

LOG = logging.getLogger(__name__)


class AttributeFilter(base.Filter):
    """This allows users to choose the pool by supplying hints to this filter.
    These are provided as attributes as part of the zone object provided at
    zone create time.

    .. code-block:: javascript
        :emphasize-lines: 3,4,5

        {
            "attributes": {
                "pool_level": "gold",
                "fast_ttl": "true",
                "pops": "global",
            },
            "email": "user@example.com",
            "name": "example.com."
        }

    The zone attributes are matched against the potential pool candidates, and
    any pools that do not match **all** hints are removed.

    .. warning::

        This should be uses in conjunction with the
        :class:`designate.scheduler.impl_filter.filters.random_filter.RandomFilter`
        in case of multiple Pools matching the filters, as without it, we will
        raise an error to the user.
        """

    name = 'attribute'
    """Name to enable in the ``[designate:central:scheduler].filters`` option
    list
    """

    def filter(self, context, pools, zone):
        try:
            zone_attributes = zone.attributes.to_dict()
        except exceptions.RelationNotLoaded:
            zone_attributes = {}

        def evaluate_pool(pool):
            try:
                pool_attributes = pool.attributes.to_dict()
            except exceptions.RelationNotLoaded:
                pool_attributes = {}

            # Remove the "pool_id" attribute, that is used in
            # PoolIDAttributeFilter. If the item is not in the dict, it is
            # fine, we should just continue.
            pool_attributes.pop('pool_id', None)

            if not pool_attributes:
                # If we did not send any attribute to filter on, we should
                # not filter the pools based on an empty set, as this will
                # return no pools.
                return True

            # Check if the keys requested exist in this pool
            if not {key for key in pool_attributes.keys()}.issuperset(
                    zone_attributes):
                LOG.debug(
                    '%(pool)s did not match list of requested attribute '
                    'keys - removing from list. Requested: %(r_key)s. Pool:'
                    '%(p_key)s',
                    {
                        'pool': pool,
                        'r_key': zone_attributes,
                        'p_key': pool_attributes
                    }
                )
                # Missing required keys - remove from the list
                return False

            for key in zone_attributes.keys():
                LOG.debug('Checking value of %s for %s', key, pool)

                pool_attr = bool_from_string(pool_attributes[key],
                                             default=pool_attributes[key])
                zone_attr = bool_from_string(zone_attributes[key],
                                             default=zone_attributes[key])

                if not pool_attr == zone_attr:
                    LOG.debug(
                        '%(pool)s did not match requested value of %(key)s. '
                        'Requested: %(r_val)s. Pool: %(p_val)s',
                        {
                            'pool': pool,
                            'key': key,
                            'r_val': zone_attr,
                            'p_val': pool_attr
                        })
                    # Value didn't match - remove from the list
                    return False

            # Pool matches list of attributes - keep
            return True

        pool_list = [pool for pool in pools if evaluate_pool(pool)]
        pools = PoolList(objects=pool_list)
        return pools
