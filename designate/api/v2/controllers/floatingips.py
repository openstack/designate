# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hpe.com>
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
from designate.common import constants
from designate import exceptions
from designate import objects
from designate.objects.adapters import DesignateAdapter

LOG = logging.getLogger(__name__)


def fip_key_to_data(key):
    m = constants.RE_FIP.match(key)

    # NOTE: Ensure that the fip matches region:floatingip_id or raise, if
    # not this will cause a 500.
    if m is None:
        msg = 'Floating IP %s is not in the format of <region>:<uuid>'
        raise exceptions.BadRequest(msg % key)
    return m.groups()


class FloatingIPController(rest.RestController):

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Floating IP PTRs for a Tenant"""
        request = pecan.request
        context = request.environ['context']

        fips = self.central_api.list_floatingips(context)

        LOG.info('Retrieved %(fips)s', {'fips': fips})

        return DesignateAdapter.render('API_v2', fips, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def patch_one(self, fip_key):
        """
        Set or unset a PTR
        """
        request = pecan.request
        response = pecan.response

        context = request.environ['context']
        body = request.body_dict

        region, id_ = fip_key_to_data(fip_key)

        fip = DesignateAdapter.parse('API_v2', body, objects.FloatingIP())

        fip.validate()

        LOG.info('Updated %(fip)s', {'fip': fip})

        fip = self.central_api.update_floatingip(context, region, id_, fip)

        response.status_int = 202

        if fip:
            return DesignateAdapter.render('API_v2', fip, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_one(self, fip_key):
        """
        Get PTR
        """
        request = pecan.request
        context = request.environ['context']

        region, id_ = fip_key_to_data(fip_key)

        fip = self.central_api.get_floatingip(context, region, id_)

        LOG.info('Retrieved %(fip)s', {'fip': fip})

        return DesignateAdapter.render('API_v2', fip, request=request)
