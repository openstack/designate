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
        name="create_zone_import",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Create Zone Import",
        operations=[
            {
                'path': '/v2/zones/tasks/imports',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_zone_imports",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="List all Zone Imports",
        operations=[
            {
                'path': '/v2/zones/tasks/imports',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_zone_import",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Get Zone Imports",
        operations=[
            {
                'path': '/v2/zones/tasks/imports/{zone_import_id}',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="update_zone_import",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Update Zone Imports",
        operations=[
            {
                'path': '/v2/zones/tasks/imports',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="delete_zone_import",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Delete a Zone Import",
        operations=[
            {
                'path': '/v2/zones/tasks/imports/{zone_import_id}',
                'method': 'GET'
            }
        ]
    )
]


def list_rules():
    return rules
