# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
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
from oslo_log import log as logging

from designate.api.v2.views import base as base_view


LOG = logging.getLogger(__name__)


class TldsView(base_view.BaseView):
    """Model a TLD API response as a python dictionary"""

    _resource_name = 'tld'
    _collection_name = 'tlds'

    def show_basic(self, context, request, tld):
        """Basic view of a tld"""
        return {
            "id": tld['id'],
            "name": tld['name'],
            "description": tld['description'],
            "created_at": tld['created_at'],
            "updated_at": tld['updated_at'],
            "links": self._get_resource_links(request, tld)
        }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('name', 'description')
        return self._load(context, request, body, valid_keys)
