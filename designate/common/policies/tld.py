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
The top-level domain API now supports system scope and default roles.
"""

deprecated_create_tld = policy.DeprecatedRule(
    name="create_tld",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_tlds = policy.DeprecatedRule(
    name="find_tlds",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_tld = policy.DeprecatedRule(
    name="get_tld",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_tld = policy.DeprecatedRule(
    name="update_tld",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_tld = policy.DeprecatedRule(
    name="delete_tld",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="create_tld",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Create Tld",
        operations=[
            {
                'path': '/v2/tlds',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_create_tld
    ),
    policy.DocumentedRuleDefault(
        name="find_tlds",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description="List Tlds",
        operations=[
            {
                'path': '/v2/tlds',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_tlds
    ),
    policy.DocumentedRuleDefault(
        name="get_tld",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description="Show Tld",
        operations=[
            {
                'path': '/v2/tlds/{tld_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_tld
    ),
    policy.DocumentedRuleDefault(
        name="update_tld",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Update Tld",
        operations=[
            {
                'path': '/v2/tlds/{tld_id}',
                'method': 'PATCH'
            }
        ],
        deprecated_rule=deprecated_update_tld
    ),
    policy.DocumentedRuleDefault(
        name="delete_tld",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Delete Tld",
        operations=[
            {
                'path': '/v2/tlds/{tld_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_delete_tld
    )
]


def list_rules():
    return rules
