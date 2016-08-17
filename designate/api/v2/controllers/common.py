# Copyright 2016 Rackspace
#
# Author: James Li <james.li@rackspace.com>
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
from designate import utils


def retrieve_matched_rrsets(context, controller_obj, zone_id, **params):
    if zone_id:
        # NOTE: We need to ensure the zone actually exists, otherwise we may
        #       return deleted recordsets instead of a zone not found
        controller_obj.central_api.get_zone(context, zone_id)

    # Extract the pagination params
    marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params, controller_obj.SORT_KEYS)

    # Extract any filter params.
    accepted_filters = (
        'name', 'type', 'ttl', 'data', 'status', 'description',)
    criterion = controller_obj._apply_filter_params(
            params, accepted_filters, {})

    # Use DB index for better performance in the case of cross zone search
    force_index = True
    if zone_id:
        criterion['zone_id'] = zone_id
        force_index = False

    recordsets = controller_obj.central_api.find_recordsets(
            context, criterion, marker, limit, sort_key, sort_dir, force_index)

    return recordsets


def get_rrset_canonical_location(request, zone_id, rrset_id):
    return '{base_url}/v2/zones/{zone_id}/recordsets/{id}'.format(
            base_url=request.host_url, zone_id=zone_id,
            id=rrset_id)
