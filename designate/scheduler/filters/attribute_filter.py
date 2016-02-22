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

from designate.scheduler.filters.base import Filter

LOG = logging.getLogger(__name__)


class AttributeFilter(Filter):
    """This allows users top choose the pool by supplying hints to this filter.
    These are provided as attributes as part of the zone object provided at
    zone create time.

    .. code-block:: javascript
        :emphasize-lines: 3,4,5

        {
            "attributes": {
                "pool_level": "gold",
                "fast_ttl": True,
                "pops": "global",
            },
            "email": "user@example.com",
            "name": "example.com."
        }

    The zone attributes are matched against the potential pool candiates, and
    any pools that do not match **all** hints are removed.

    .. warning::

        This filter is disabled currently, and should not be used.
        It will be enabled at a later date.

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
        # FIXME (graham) actually filter on attributes
        return pools
