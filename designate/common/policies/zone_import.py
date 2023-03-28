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
The zone import API now supports system scope and default roles.
"""

deprecated_create_zone_import = policy.DeprecatedRule(
    name="create_zone_import",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_zone_imports = policy.DeprecatedRule(
    name="find_zone_imports",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_zone_import = policy.DeprecatedRule(
    name="get_zone_import",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_zone_import = policy.DeprecatedRule(
    name="update_zone_import",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_zone_import = policy.DeprecatedRule(
    name="delete_zone_import",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="create_zone_import",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Create Zone Import",
        operations=[
            {
                'path': '/v2/zones/tasks/imports',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_create_zone_import
    ),
    policy.DocumentedRuleDefault(
        name="find_zone_imports",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description="List all Zone Imports",
        operations=[
            {
                'path': '/v2/zones/tasks/imports',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_zone_imports
    ),
    policy.DocumentedRuleDefault(
        name="get_zone_import",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description="Get Zone Imports",
        operations=[
            {
                'path': '/v2/zones/tasks/imports/{zone_import_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_zone_import
    ),
    policy.DocumentedRuleDefault(
        name="update_zone_import",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Update Zone Imports",
        operations=[
            {
                'path': '/v2/zones/tasks/imports',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_update_zone_import
    ),
    policy.DocumentedRuleDefault(
        name="delete_zone_import",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Delete a Zone Import",
        operations=[
            {
                'path': '/v2/zones/tasks/imports/{zone_import_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_delete_zone_import
    )
]


def list_rules():
    return rules
