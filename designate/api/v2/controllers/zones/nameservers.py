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
from oslo_log import log as logging
import pecan

from designate.api.v2.controllers import rest
from designate.objects.adapters import DesignateAdapter
from designate import utils

LOG = logging.getLogger(__name__)


class NameServersController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid("zone_id")
    def get_all(self, zone_id):
        """List NameServers for Zone"""
        request = pecan.request
        context = request.environ['context']

        # This is a work around to overcome the fact that pool ns_records list
        # object have 2 different representations in the v2 API

        ns_records = self.central_api.get_zone_ns_records(context, zone_id)

        LOG.info("Created %(ns_records)s", {'ns_records': ns_records})

        return {
            "nameservers": DesignateAdapter.render('API_v2', ns_records,
                                                   request=request)}
