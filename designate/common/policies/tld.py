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
        name="create_tld",
        check_str=base.RULE_ADMIN,
        description="Create Tld",
        operations=[
            {
                'path': '/v2/tlds',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_tlds",
        check_str=base.RULE_ADMIN,
        description="List Tlds",
        operations=[
            {
                'path': '/v2/tlds',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_tld",
        check_str=base.RULE_ADMIN,
        description="Show Tld",
        operations=[
            {
                'path': '/v2/tlds/{tld_id}',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="update_tld",
        check_str=base.RULE_ADMIN,
        description="Update Tld",
        operations=[
            {
                'path': '/v2/tlds/{tld_id}',
                'method': 'PATCH'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="delete_tld",
        check_str=base.RULE_ADMIN,
        description="Delete Tld",
        operations=[
            {
                'path': '/v2/tlds/{tld_id}',
                'method': 'DELETE'
            }
        ]
    )
]


def list_rules():
    return rules
