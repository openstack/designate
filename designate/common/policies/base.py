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


DEPRECATED_REASON = """
The designate API now supports system scope and default roles.
"""

RULE_ANY = "@"

# Generic policy check string for system administrators. These are the people
# who need the highest level of authorization to operate the deployment.
# They're allowed to create, read, update, or delete any system-specific
# resource. They can also operate on project-specific resources where
# applicable (e.g., cleaning up blacklists)
SYSTEM_ADMIN = 'role:admin'

# Generic policy check string for read-only access to system-level resources.
# This persona is useful for someone who needs access for auditing or even
# support. These uses are also able to view project-specific resources where
# applicable (e.g., listing all pools)
SYSTEM_READER = 'role:admin'

# This check string is reserved for actions that require the highest level of
# authorization on a project or resources within the project
PROJECT_ADMIN = 'role:admin and project_id:%(project_id)s'

# This check string is the primary use case for typical end-users, who are
# working with resources that belong to a project (e.g., creating DNS zones)
PROJECT_MEMBER = 'role:member and project_id:%(project_id)s'

# This check string should only be used to protect read-only project-specific
# resources. It should not be used to protect APIs that make writable changes.
PROJECT_READER = 'role:reader and project_id:%(project_id)s'

# The following are common composite check strings that are useful for
# protecting APIs designed to operate with multiple scopes
SYSTEM_ADMIN_OR_PROJECT_MEMBER = (
    '(' + SYSTEM_ADMIN + ') or (' + PROJECT_MEMBER + ')'
)
SYSTEM_OR_PROJECT_READER = (
    '(' + SYSTEM_READER + ') or (' + PROJECT_READER + ')'
)

# Designate specific "secure RBAC" rules
ALL_TENANTS = 'True:%(all_tenants)s'

ALL_TENANTS_READER = ALL_TENANTS + ' and role:reader'

SYSTEM_OR_PROJECT_READER_OR_ALL_TENANTS_READER = (
    '(' + SYSTEM_READER + ') or (' + PROJECT_READER + ') or (' +
    ALL_TENANTS_READER + ')'
)

SYSTEM_OR_PROJECT_READER_OR_SHARED = (
        SYSTEM_OR_PROJECT_READER + ' or (\'True\':%(zone_shared)s)'
)

RULE_ZONE_TRANSFER = (
    '(' + SYSTEM_ADMIN_OR_PROJECT_MEMBER + ') or '
    'project_id:%(target_project_id)s or '
    'None:%(target_project_id)s')


# Deprecated in Wallaby as part of the "secure RBAC" work.
# TODO(johnsom) remove when the deprecated RBAC rules are removed.
RULE_ADMIN = 'rule:admin'
RULE_ADMIN_OR_OWNER = 'rule:admin_or_owner'
LEGACY_RULE_ZONE_TRANSFER = (
    "rule:admin_or_owner OR "
    "project_id:%(target_tenant_id)s "
    "OR None:%(target_tenant_id)s"
)
RULE_ADMIN_OR_OWNER_OR_SHARED = (
        RULE_ADMIN_OR_OWNER + ' or (\'True\':%(zone_shared)s)'
)

deprecated_default = policy.DeprecatedRule(
    name="default",
    check_str=RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

rules = [
    # TODO(johnsom) remove when the deprecated RBAC rules are removed.
    policy.RuleDefault(
        name="admin",
        check_str="role:admin or is_admin:True"),
    # TODO(johnsom) remove when the deprecated RBAC rules are removed.
    policy.RuleDefault(
        name="owner",
        check_str="project_id:%(tenant_id)s"),
    # TODO(johnsom) remove when the deprecated RBAC rules are removed.
    policy.RuleDefault(
        name="admin_or_owner",
        check_str="rule:admin or rule:owner"),

    # Default policy
    policy.RuleDefault(
        name="default",
        check_str=SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        deprecated_rule=deprecated_default),
]


def list_rules():
    return rules
