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
        name="create_blacklist",
        check_str=base.RULE_ADMIN,
        description='Create blacklist.',
        operations=[
            {
                'path': '/v2/blacklists',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_blacklist",
        check_str=base.RULE_ADMIN,
        description='Find blacklist.',
        operations=[
            {
                'path': '/v2/blacklists',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_blacklists",
        check_str=base.RULE_ADMIN,
        description='Find blacklists.',
        operations=[
            {
                'path': '/v2/blacklists',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_blacklist",
        check_str=base.RULE_ADMIN,
        description='Get blacklist.',
        operations=[
            {
                'path': '/v2/blacklists/{blacklist_id}',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="update_blacklist",
        check_str=base.RULE_ADMIN,
        description='Update blacklist.',
        operations=[
            {
                'path': '/v2/blacklists/{blacklist_id}',
                'method': 'PATCH'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="delete_blacklist",
        check_str=base.RULE_ADMIN,
        description='Delete blacklist.',
        operations=[
            {
                'path': '/v2/blacklists/{blacklist_id}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="use_blacklisted_zone",
        check_str=base.RULE_ADMIN,
        description='Allowed bypass the blacklist.',
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
