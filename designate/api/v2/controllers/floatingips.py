# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
import re

import pecan

from designate import exceptions
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate.api.v2.controllers import rest


FIP_REGEX = '^(?P<region>[A-Za-z0-9\\.\\-_]{1,100}):' \
            '(?P<id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-' \
            '[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$'


def fip_key_to_data(key):
    m = re.match(FIP_REGEX, key)

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

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.list_floatingips(context),
            request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def patch_one(self, fip_key):
        """
        Set or unset a PTR
        """
        request = pecan.request
        context = request.environ['context']
        try:
            body = request.body_dict
        except Exception as e:
            if e.message != 'TODO: Unsupported Content Type':
                raise
            else:
                # Got a blank body
                body = dict()

        region, id_ = fip_key_to_data(fip_key)

        fip = DesignateAdapter.parse('API_v2', body, objects.FloatingIP())

        fip.validate()

        fip = self.central_api.update_floatingip(context, region, id_, fip)

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

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.get_floatingip(context, region, id_),
            request=request)
