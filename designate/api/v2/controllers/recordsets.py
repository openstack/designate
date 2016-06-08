# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import pecan
from oslo_log import log as logging

from designate import utils
from designate.api.v2.controllers import common
from designate.api.v2.controllers import rest
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI

LOG = logging.getLogger(__name__)


class RecordSetsViewController(rest.RestController):
    SORT_KEYS = ['created_at', 'updated_at', 'zone_id', 'tenant_id',
                 'name', 'type', 'ttl']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('recordset_id')
    def get_one(self, recordset_id):
        """Get RecordSet"""
        request = pecan.request
        context = request.environ['context']

        rrset = self.central_api.get_recordset(context, None, recordset_id)

        LOG.info(_LI("Retrieved %(recordset)s"), {'recordset': rrset})

        canonical_loc = common.get_rrset_canonical_location(request,
                                                            rrset.zone_id,
                                                            recordset_id)
        pecan.core.redirect(location=canonical_loc, code=301)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List RecordSets"""
        request = pecan.request
        context = request.environ['context']
        recordsets = common.retrieve_matched_rrsets(context, self, None,
                                                    **params)

        LOG.info(_LI("Retrieved %(recordsets)s"), {'recordsets': recordsets})

        return DesignateAdapter.render('API_v2', recordsets, request=request)
