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
    policy.RuleDefault(
        name="create_pool",
        check_str=base.RULE_ADMIN,
        description='Create pool.'),
    policy.DocumentedRuleDefault(
        name="find_pools",
        check_str=base.RULE_ADMIN,
        description='Find pool.',
        operations=[
            {
                'path': '/v2/pools',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_pool",
        check_str=base.RULE_ADMIN,
        description='Find pools.',
        operations=[
            {
                'path': '/v2/pools',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_pool",
        check_str=base.RULE_ADMIN,
        description='Get pool.',
        operations=[
            {
                'path': '/v2/pools/{pool_id}',
                'method': 'GET'
            }
        ]
    ),
    policy.RuleDefault(
        name="update_pool",
        check_str=base.RULE_ADMIN,
        description='Update pool.'),
    policy.RuleDefault(
        name="delete_pool",
        check_str=base.RULE_ADMIN,
        description='Delete pool.'
    ),
    policy.DocumentedRuleDefault(
        name="zone_create_forced_pool",
        check_str=base.RULE_ADMIN,
        description='load and set the pool to the one provided in the Zone attributes.',  # noqa
        operations=[
            {
                'path': '/v2/zones',
                'method': 'POST'
            }
        ]
    )
]


def list_rules():
    return rules
