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
from designate import objects
from designate.api.v2.views import base as base_view
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class RecordSetsView(base_view.BaseView):
    """Model a Zone API response as a python dictionary"""

    _resource_name = 'recordset'
    _collection_name = 'recordsets'

    def _get_base_href(self, parents=None):
        assert len(parents) == 1

        href = "%s/v2/zones/%s/recordsets" % (self.base_uri, parents[0])

        return href.rstrip('?')

    def show_basic(self, context, request, recordset):
        """Basic view of a recordset"""

        return {
            "id": recordset['id'],
            "zone_id": recordset['domain_id'],
            "name": recordset['name'],
            "type": recordset['type'],
            "ttl": recordset['ttl'],
            "records": [r.data for r in recordset['records']],
            "description": recordset['description'],
            "version": recordset['version'],
            "created_at": recordset['created_at'],
            "updated_at": recordset['updated_at'],
            "links": self._get_resource_links(request, recordset,
                                              [recordset['domain_id']])
        }

    def load(self, context, request, body):
        """Extract a "central" compatible dict from an API call"""
        valid_keys = ('name', 'type', 'ttl', 'description', 'records')

        result = self._load(context, request, body, valid_keys)

        if 'records' in result:
            result['records'] = objects.RecordList(objects=[
                objects.Record(data=r) for r in result['records']
            ])

        return result
