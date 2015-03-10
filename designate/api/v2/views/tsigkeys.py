# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

from oslo_log import log as logging

from designate.api.v2.views import base as base_view


LOG = logging.getLogger(__name__)


class TsigKeysView(base_view.BaseView):
    """Model a TsigKey API response as a python dictionary"""

    _resource_name = 'tsigkey'
    _collection_name = 'tsigkeys'

    def show_basic(self, context, request, tsigkey):
        """Detailed view of a TsigKey"""
        return {
            "id": tsigkey['id'],

            "name": tsigkey['name'],
            "algorithm": tsigkey['algorithm'],
            "secret": tsigkey['secret'],
            "scope": tsigkey['scope'],
            "resource_id": tsigkey['resource_id'],

            "created_at": tsigkey['created_at'],
            "updated_at": tsigkey['updated_at'],
            "links": self._get_resource_links(request, tsigkey)
        }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('name', 'algorithm', 'secret', 'scope', 'resource_id')
        return self._load(context, request, body, valid_keys)
