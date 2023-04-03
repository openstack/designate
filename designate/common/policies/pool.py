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
The pool API now supports system scope and default roles.
"""

deprecated_create_pool = policy.DeprecatedRule(
    name="create_pool",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_pools = policy.DeprecatedRule(
    name="find_pools",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_pool = policy.DeprecatedRule(
    name="find_pool",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_pool = policy.DeprecatedRule(
    name="get_pool",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_pool = policy.DeprecatedRule(
    name="update_pool",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_pool = policy.DeprecatedRule(
    name="delete_pool",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_zone_created_forced_pool = policy.DeprecatedRule(
    name="zone_create_forced_pool",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.RuleDefault(
        name="create_pool",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Create pool.',
        deprecated_rule=deprecated_create_pool
    ),
    policy.DocumentedRuleDefault(
        name="find_pools",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description='Find pool.',
        operations=[
            {
                'path': '/v2/pools',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_pools
    ),
    policy.DocumentedRuleDefault(
        name="find_pool",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description='Find pools.',
        operations=[
            {
                'path': '/v2/pools',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_pool
    ),
    policy.DocumentedRuleDefault(
        name="get_pool",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description='Get pool.',
        operations=[
            {
                'path': '/v2/pools/{pool_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_pool
    ),
    policy.RuleDefault(
        name="update_pool",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Update pool.',
        deprecated_rule=deprecated_update_pool
    ),
    policy.RuleDefault(
        name="delete_pool",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Delete pool.',
        deprecated_rule=deprecated_delete_pool
    ),
    policy.DocumentedRuleDefault(
        name="zone_create_forced_pool",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='load and set the pool to the one provided in the Zone attributes.',  # noqa
        operations=[
            {
                'path': '/v2/zones',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_zone_created_forced_pool
    )
]


def list_rules():
    return rules
