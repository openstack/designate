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
        name="get_quotas",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="View Current Project's Quotas.",
        operations=[
            {
                'path': '/v2/quotas',
                'method': 'GET'
            }
        ]
    ),
    policy.RuleDefault(
        name="get_quota",
        check_str=base.RULE_ADMIN_OR_OWNER
    ),
    policy.DocumentedRuleDefault(
        name="set_quota",
        check_str=base.RULE_ADMIN,
        description='Set Quotas.',
        operations=[
            {
                'path': '/v2/quotas/{project_id}',
                'method': 'PATCH'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="reset_quotas",
        check_str=base.RULE_ADMIN,
        description='Reset Quotas.',
        operations=[
            {
                'path': '/v2/quotas/{project_id}',
                'method': 'DELETE'
            }
        ]
    ),
]


def list_rules():
    return rules
