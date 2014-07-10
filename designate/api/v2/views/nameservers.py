# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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

from designate.api.v2.views import base as base_view
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class NameServerView(base_view.BaseView):
    """Model a NameServer API response as a python dictionary"""

    _resource_name = 'nameserver'
    _collection_name = 'nameservers'

    def _get_base_href(self, parents=None):
        assert len(parents) == 1

        href = "%s/v2/zones/%s/nameservers" % (self.base_uri, parents[0])

        return href.rstrip('?')

    def show_basic(self, context, request, nameserver):
        """Basic view of a nameserver"""
        return {
            "id": nameserver["id"],
            "name": nameserver["name"]
        }
