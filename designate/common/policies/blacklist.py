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
The blacklist API now supports system scope and default roles.
"""

deprecated_create_blacklist = policy.DeprecatedRule(
    name="create_blacklist",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_blacklists = policy.DeprecatedRule(
    name="find_blacklists",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_blacklist = policy.DeprecatedRule(
    name="get_blacklist",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_blacklist = policy.DeprecatedRule(
    name="update_blacklist",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_blacklist = policy.DeprecatedRule(
    name="delete_blacklist",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_use_blacklisted_zone = policy.DeprecatedRule(
    name="use_blacklisted_zone",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="create_blacklist",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Create blacklist.',
        operations=[
            {
                'path': '/v2/blacklists',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_create_blacklist
    ),
    policy.DocumentedRuleDefault(
        name="find_blacklists",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description='Find blacklists.',
        operations=[
            {
                'path': '/v2/blacklists',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_blacklists
    ),
    policy.DocumentedRuleDefault(
        name="get_blacklist",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description='Get blacklist.',
        operations=[
            {
                'path': '/v2/blacklists/{blacklist_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_blacklist
    ),
    policy.DocumentedRuleDefault(
        name="update_blacklist",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Update blacklist.',
        operations=[
            {
                'path': '/v2/blacklists/{blacklist_id}',
                'method': 'PATCH'
            }
        ],
        deprecated_rule=deprecated_update_blacklist
    ),
    policy.DocumentedRuleDefault(
        name="delete_blacklist",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Delete blacklist.',
        operations=[
            {
                'path': '/v2/blacklists/{blacklist_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_delete_blacklist
    ),
    policy.DocumentedRuleDefault(
        name="use_blacklisted_zone",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Allowed bypass the blacklist.',
        operations=[
            {
                'path': '/v2/zones',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_use_blacklisted_zone
    )
]


def list_rules():
    return rules
