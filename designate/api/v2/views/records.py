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


class RecordsView(base_view.BaseView):
    """ Model a Record API response as a python dictionary """

    _resource_name = 'record'
    _collection_name = 'records'

    def _get_base_href(self, parents=None):
        assert len(parents) == 2

        href = "%s/v2/zones/%s/recordsets/%s/records" % (self.base_uri,
                                                         parents[0],
                                                         parents[1])

        return href.rstrip('?')

    def show_basic(self, context, request, record):
        """ Basic view of a record """
        return {
            "id": record['id'],
            "recordset_id": record['recordset_id'],
            "data": record['data'],
            "description": record['description'],
            "version": record['version'],
            "created_at": record['created_at'],
            "updated_at": record['updated_at'],
            "links": self._get_resource_links(
                request, record,
                [record['domain_id'], record['recordset_id']])
        }

    def load(self, context, request, body):
        """ Extract a "central" compatible dict from an API call """
        valid_keys = ('data', 'description')
        return self._load(context, request, body, valid_keys)
