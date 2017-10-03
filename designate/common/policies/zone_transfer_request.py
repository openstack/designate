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
        name="create_zone_transfer_request",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Create Zone Transfer Accept",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/transfer_requests',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_zone_transfer_request",
        check_str=base.RULE_ZONE_TRANSFER,
        description="Show a Zone Transfer Request",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_request_id}',  # noqa
                'method': 'GET'
            }, {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_request_id}',  # noqa
                'method': 'PATCH'
            }
        ]
    ),
    policy.RuleDefault(
        name="get_zone_transfer_request_detailed",
        check_str=base.RULE_ADMIN_OR_OWNER
    ),
    policy.DocumentedRuleDefault(
        name="find_zone_transfer_requests",
        check_str=base.RULE_ANY,
        description="List Zone Transfer Requests",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests',
                'method': 'GET'
            }
        ]
    ),
    policy.RuleDefault(
        name="find_zone_transfer_request",
        check_str=base.RULE_ANY
    ),
    policy.DocumentedRuleDefault(
        name="update_zone_transfer_request",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Update a Zone Transfer Request",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_request_id}',  # noqa
                'method': 'PATCH'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="delete_zone_transfer_request",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Delete a Zone Transfer Request",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_request_id}',  # noqa
                'method': 'DELETE'
            }
        ]
    )
]


def list_rules():
    return rules
