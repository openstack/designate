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
The zone API now supports system scope and default roles.
"""

deprecated_create_zone = policy.DeprecatedRule(
    name="create_zone",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_zones = policy.DeprecatedRule(
    name="get_zones",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_zone = policy.DeprecatedRule(
    name="get_zone",
    check_str=base.RULE_ADMIN_OR_OWNER_OR_SHARED,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_zone_servers = policy.DeprecatedRule(
    name="get_zone_servers",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_zone_ns_records = policy.DeprecatedRule(
    name="get_zone_ns_records",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_zones = policy.DeprecatedRule(
    name="find_zones",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_zone = policy.DeprecatedRule(
    name="update_zone",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_zone = policy.DeprecatedRule(
    name="delete_zone",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_xfr_zone = policy.DeprecatedRule(
    name="xfr_zone",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_abandon_zone = policy.DeprecatedRule(
    name="abandon_zone",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_count_zones = policy.DeprecatedRule(
    name="count_zones",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_count_zones_pending_notify = policy.DeprecatedRule(
    name="count_zones_pending_notify",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_purge_zones = policy.DeprecatedRule(
    name="purge_zones",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_pool_move_zone = policy.DeprecatedRule(
    name="pool_move_zone",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="create_zone",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Create Zone",
        operations=[
            {
                'path': '/v2/zones',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_create_zone
    ),
    policy.RuleDefault(
        name="get_zones",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_get_zones
    ),
    policy.DocumentedRuleDefault(
        name="get_zone",
        check_str=base.SYSTEM_OR_PROJECT_READER_OR_SHARED,
        scope_types=[constants.PROJECT],
        description="Get Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_zone
    ),
    policy.RuleDefault(
        name="get_zone_servers",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_get_zone_servers
    ),
    policy.DocumentedRuleDefault(
        name="get_zone_ns_records",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description="Get the Name Servers for a Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/nameservers',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_zone_ns_records
    ),
    policy.DocumentedRuleDefault(
        name="find_zones",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description="List existing zones",
        operations=[
            {
                'path': '/v2/zones',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_zones
    ),
    policy.DocumentedRuleDefault(
        name="update_zone",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Update Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}',
                'method': 'PATCH'
            }
        ],
        deprecated_rule=deprecated_update_zone
    ),
    policy.DocumentedRuleDefault(
        name="delete_zone",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Delete Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_delete_zone
    ),
    policy.DocumentedRuleDefault(
        name="xfr_zone",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Manually Trigger an Update of a Secondary Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/xfr',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_xfr_zone
    ),
    policy.DocumentedRuleDefault(
        name="abandon_zone",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Abandon Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/abandon',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_abandon_zone
    ),
    policy.RuleDefault(
        name="count_zones",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_count_zones
    ),
    policy.RuleDefault(
        name="count_zones_pending_notify",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_count_zones_pending_notify
    ),
    policy.RuleDefault(
        name="purge_zones",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_purge_zones
    ),
    policy.DocumentedRuleDefault(
        name="pool_move_zone",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Pool Move Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/pool_move',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_pool_move_zone,
    )
]


def list_rules():
    return rules
