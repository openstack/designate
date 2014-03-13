# Copyright 2014 Rackspace
#
# Author: Betsy Luzader <betsy.luzader@rackspace.com>
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


class BlacklistsView(base_view.BaseView):
    """ Model a Blacklist API response as a python dictionary """

    _resource_name = 'blacklist'
    _collection_name = 'blacklists'

    def show_basic(self, context, request, blacklist):
        """ Detailed view of a blacklisted zone """
        return {
            "id": blacklist['id'],
            "pattern": blacklist['pattern'],
            "description": blacklist['description'],
            "created_at": blacklist['created_at'],
            "updated_at": blacklist['updated_at'],
            "links": self._get_resource_links(request, blacklist)
        }

    def load(self, context, request, body):
        """ Extract a "central" compatible dict from an API call """
        valid_keys = ('pattern', 'description')
        return self._load(context, request, body, valid_keys)
