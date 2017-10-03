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
        name="create_zone_transfer_accept",
        check_str=base.RULE_ZONE_TRANSFER,
        description="Create Zone Transfer Accept",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_accepts',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_zone_transfer_accept",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Get Zone Transfer Accept",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_accept_id}',  # noqa
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_zone_transfer_accepts",
        check_str=base.RULE_ADMIN,
        description="List Zone Transfer Accepts",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_accepts',
                'method': 'GET'
            }
        ]
    ),
    policy.RuleDefault(
        name="find_zone_transfer_accept",
        check_str=base.RULE_ADMIN
    ),
    policy.DocumentedRuleDefault(
        name="update_zone_transfer_accept",
        check_str=base.RULE_ADMIN,
        description="Update a Zone Transfer Accept",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_accepts',
                'method': 'POST'
            }
        ]
    ),
    policy.RuleDefault(
        name="delete_zone_transfer_accept",
        check_str=base.RULE_ADMIN
    )
]


def list_rules():
    return rules
