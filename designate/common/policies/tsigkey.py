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


from oslo_log import versionutils
from oslo_policy import policy

from designate.common import constants
from designate.common.policies import base

DEPRECATED_REASON = """
The tsigkey API now supports system scope and default roles.
"""

deprecated_create_tsigkey = policy.DeprecatedRule(
    name="create_tsigkey",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_tsigkeys = policy.DeprecatedRule(
    name="find_tsigkeys",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_tsigkey = policy.DeprecatedRule(
    name="get_tsigkey",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_tsigkey = policy.DeprecatedRule(
    name="update_tsigkey",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_tsigkey = policy.DeprecatedRule(
    name="delete_tsigkey",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="create_tsigkey",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Create Tsigkey",
        operations=[
            {
                'path': '/v2/tsigkeys',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_create_tsigkey
    ),
    policy.DocumentedRuleDefault(
        name="find_tsigkeys",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description="List Tsigkeys",
        operations=[
            {
                'path': '/v2/tsigkeys',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_tsigkeys
    ),
    policy.DocumentedRuleDefault(
        name="get_tsigkey",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description="Show a Tsigkey",
        operations=[
            {
                'path': '/v2/tsigkeys/{tsigkey_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_tsigkey
    ),
    policy.DocumentedRuleDefault(
        name="update_tsigkey",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Update Tsigkey",
        operations=[
            {
                'path': '/v2/tsigkeys/{tsigkey_id}',
                'method': 'PATCH'
            }
        ],
        deprecated_rule=deprecated_update_tsigkey
    ),
    policy.DocumentedRuleDefault(
        name="delete_tsigkey",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Delete a Tsigkey",
        operations=[
            {
                'path': '/v2/tsigkeys/{tsigkey_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_delete_tsigkey
    )
]


def list_rules():
    return rules
