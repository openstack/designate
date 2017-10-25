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


from oslo_policy import policy

from designate.common.policies import base

rules = [
    policy.DocumentedRuleDefault(
        name="zone_export",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Retrive a Zone Export from the Designate Datastore",
        operations=[
            {
                'path': '/v2/zones/tasks/exports/{zone_export_id}/export',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="create_zone_export",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Create Zone Export",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/export',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_zone_exports",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="List Zone Exports",
        operations=[
            {
                'path': '/v2/zones/tasks/exports',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_zone_export",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Get Zone Exports",
        operations=[
            {
                'path': '/v2/zones/tasks/exports/{zone_export_id}',
                'method': 'GET'
            }, {
                'path': '/v2/zones/tasks/exports/{zone_export_id}/export',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="update_zone_export",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Update Zone Exports",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/export',
                'method': 'POST'
            }
        ]
    )
]


def list_rules():
    return rules
