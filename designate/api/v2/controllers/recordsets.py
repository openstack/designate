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
import pecan
from designate.api.v2.controllers import rest
from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class RecordSetsController(rest.RestController):
    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, zone_id, recordset_id):
        """ Get RecordSet """
        pass

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, zone_id):
        """ List RecordSets """
        pass

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self, zone_id):
        """ Create RecordSet """
        pass

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    def patch_one(self, zone_id, recordset_id):
        """ Update RecordSet """
        pass

    @pecan.expose(template='json:', content_type='application/json')
    def delete_one(self, zone_id, recordset_id):
        """ Delete RecordSet """
        pass
