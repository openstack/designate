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
The shared zones API now supports system scope and default roles.
"""

deprecated_get_shared_zone = policy.DeprecatedRule(
    name="get_zone_share",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

deprecated_share_zone = policy.DeprecatedRule(
    name="share_zone",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

deprecated_find_project_zone_share = policy.DeprecatedRule(
    name="find_project_zone_share",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

deprecated_unshare_zone = policy.DeprecatedRule(
    name="unshare_zone",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

rules = [
    policy.DocumentedRuleDefault(
        name="get_zone_share",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Get a Zone Share",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/shares/{zone_share_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_shared_zone
    ),
    policy.DocumentedRuleDefault(
        name="share_zone",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Share a Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/shares',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_share_zone
    ),
    policy.DocumentedRuleDefault(
        name="find_zone_shares",
        # Using rule ANY here because the search criteria will narrow the
        # results appropriate for the API call.
        check_str=base.RULE_ANY,
        description="List Shared Zones",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/shares',
                'method': 'GET'
            }
        ]
    ),
    policy.RuleDefault(
        name="find_project_zone_share",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Check the can query for a specific projects shares.",
        deprecated_rule=deprecated_find_project_zone_share
    ),
    policy.DocumentedRuleDefault(
        name="unshare_zone",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Unshare Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/shares/{shared_zone_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_unshare_zone
    )
]


def list_rules():
    return rules
