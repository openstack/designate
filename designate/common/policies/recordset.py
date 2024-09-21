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
The record set API now supports system scope and default roles.
"""

# Deprecated in Wallaby as part of the "secure RBAC" work.
# TODO(johnsom) remove when the deprecated RBAC rules are removed.
RULE_ZONE_PRIMARY_OR_ADMIN = (
    "('PRIMARY':%(zone_type)s and rule:admin_or_owner) "
    "OR ('SECONDARY':%(zone_type)s AND is_admin:True)")

RULE_ZONE_PRIMARY_OR_ADMIN_OR_SHARED = (
    "('PRIMARY':%(zone_type)s AND (rule:admin_or_owner OR "
    "'True':%(zone_shared)s)) "
    "OR ('SECONDARY':%(zone_type)s AND is_admin:True)")

RULE_ADMIN_OR_OWNER_PRIMARY = (
    "rule:admin or (\'PRIMARY\':%(zone_type)s and "
    "(rule:owner or project_id:%(recordset_project_id)s))"
)


deprecated_create_recordset = policy.DeprecatedRule(
    name="create_recordset",
    check_str=RULE_ZONE_PRIMARY_OR_ADMIN_OR_SHARED,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_recordsets = policy.DeprecatedRule(
    name="get_recordsets",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_recordset = policy.DeprecatedRule(
    name="get_recordset",
    check_str=base.RULE_ADMIN_OR_OWNER_OR_SHARED,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_recordset = policy.DeprecatedRule(
    name="find_recordset",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_recordsets = policy.DeprecatedRule(
    name="find_recordsets",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_recordset = policy.DeprecatedRule(
    name="update_recordset",
    check_str=RULE_ADMIN_OR_OWNER_PRIMARY,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_recordset = policy.DeprecatedRule(
    name="delete_recordset",
    check_str=RULE_ADMIN_OR_OWNER_PRIMARY,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_count_recordset = policy.DeprecatedRule(
    name="count_recordset",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

PROJECT_MEMBER_AND_PRIMARY_ZONE = (
    '(' + base.PROJECT_MEMBER + ') and (\'PRIMARY\':%(zone_type)s)'
)
SYSTEM_ADMIN_AND_PRIMARY_ZONE = (
    '(' + base.SYSTEM_ADMIN + ') and (\'PRIMARY\':%(zone_type)s)'
)
SYSTEM_ADMIN_AND_SECONDARY_ZONE = (
    '(' + base.SYSTEM_ADMIN + ') and (\'SECONDARY\':%(zone_type)s)'
)
SHARED_AND_PRIMARY_ZONE = (
    '(\'True\':%(zone_shared)s) and (\'PRIMARY\':%(zone_type)s)'
)
RECORDSET_MEMBER_AND_PRIMARY_ZONE = (
    'role:member and (project_id:%(recordset_project_id)s) and '
    '(\'PRIMARY\':%(zone_type)s)'
)


SYSTEM_ADMIN_OR_PROJECT_MEMBER_ZONE_TYPE = ' or '.join(
    [PROJECT_MEMBER_AND_PRIMARY_ZONE,
     SYSTEM_ADMIN_AND_PRIMARY_ZONE,
     SYSTEM_ADMIN_AND_SECONDARY_ZONE,
     SHARED_AND_PRIMARY_ZONE]
)

SYSTEM_ADMIN_OR_PROJECT_MEMBER_RECORD_OWNER_ZONE_TYPE = ' or '.join(
    [PROJECT_MEMBER_AND_PRIMARY_ZONE,
     SYSTEM_ADMIN_AND_PRIMARY_ZONE,
     SYSTEM_ADMIN_AND_SECONDARY_ZONE,
     RECORDSET_MEMBER_AND_PRIMARY_ZONE]
)


rules = [
    policy.DocumentedRuleDefault(
        name="create_recordset",
        check_str=SYSTEM_ADMIN_OR_PROJECT_MEMBER_ZONE_TYPE,
        scope_types=[constants.PROJECT],
        description="Create Recordset",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_create_recordset
    ),
    policy.RuleDefault(
        name="get_recordsets",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_get_recordsets
    ),
    policy.DocumentedRuleDefault(
        name="get_recordset",
        check_str=base.SYSTEM_OR_PROJECT_READER_OR_SHARED,
        scope_types=[constants.PROJECT],
        description="Get recordset",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_recordset
    ),
    policy.RuleDefault(
        name="find_recordset",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description="List a Recordset in a Zone",
        deprecated_rule=deprecated_find_recordset
    ),
    policy.DocumentedRuleDefault(
        name="find_recordsets",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description="List Recordsets in a Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets',
                'method': 'GET'
            },
        ],
        deprecated_rule=deprecated_find_recordsets
    ),
    policy.DocumentedRuleDefault(
        name="update_recordset",
        check_str=SYSTEM_ADMIN_OR_PROJECT_MEMBER_RECORD_OWNER_ZONE_TYPE,
        scope_types=[constants.PROJECT],
        description="Update recordset",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'PUT'
            }
        ],
        deprecated_rule=deprecated_update_recordset
    ),
    policy.DocumentedRuleDefault(
        name="delete_recordset",
        check_str=SYSTEM_ADMIN_OR_PROJECT_MEMBER_RECORD_OWNER_ZONE_TYPE,
        scope_types=[constants.PROJECT],
        description="Delete RecordSet",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_delete_recordset
    ),
    policy.RuleDefault(
        name="count_recordset",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description="Count recordsets",
        deprecated_rule=deprecated_count_recordset,
    )
]


def list_rules():
    return rules
