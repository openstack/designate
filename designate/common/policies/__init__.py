# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Borrowed from Zun


import itertools

from designate.common.policies import base
from designate.common.policies import blacklist
from designate.common.policies import context
from designate.common.policies import pool
from designate.common.policies import quota
from designate.common.policies import record
from designate.common.policies import recordset
from designate.common.policies import service_status
from designate.common.policies import shared_zones
from designate.common.policies import tenant
from designate.common.policies import tld
from designate.common.policies import tsigkey
from designate.common.policies import zone
from designate.common.policies import zone_export
from designate.common.policies import zone_import
from designate.common.policies import zone_transfer_accept
from designate.common.policies import zone_transfer_request


def list_rules():
    return itertools.chain(
        base.list_rules(),
        blacklist.list_rules(),
        context.list_rules(),
        pool.list_rules(),
        quota.list_rules(),
        record.list_rules(),
        recordset.list_rules(),
        service_status.list_rules(),
        shared_zones.list_rules(),
        tenant.list_rules(),
        tld.list_rules(),
        tsigkey.list_rules(),
        zone.list_rules(),
        zone_export.list_rules(),
        zone_import.list_rules(),
        zone_transfer_accept.list_rules(),
        zone_transfer_request.list_rules(),
    )
