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
The zone transfer request API now supports system scope and default roles.
"""

deprecated_create_zone_transfer_request = policy.DeprecatedRule(
    name="create_zone_transfer_request",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_zone_transfer_request = policy.DeprecatedRule(
    name="get_zone_transfer_request",
    check_str=base.LEGACY_RULE_ZONE_TRANSFER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_get_zone_transfer_request_detailed = policy.DeprecatedRule(
    name="get_zone_transfer_request_detailed",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_zone_transfer_request = policy.DeprecatedRule(
    name="update_zone_transfer_request",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_zone_transfer_request = policy.DeprecatedRule(
    name="delete_zone_transfer_request",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="create_zone_transfer_request",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Create Zone Transfer Accept",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/transfer_requests',
                'method': 'POST'
            }
        ],
        deprecated_rule=deprecated_create_zone_transfer_request
    ),
    policy.DocumentedRuleDefault(
        name="get_zone_transfer_request",
        check_str=base.RULE_ZONE_TRANSFER,
        scope_types=[constants.PROJECT],
        description="Show a Zone Transfer Request",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_request_id}',  # noqa
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_zone_transfer_request
    ),
    policy.RuleDefault(
        name="get_zone_transfer_request_detailed",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_create_zone_transfer_request
    ),
    policy.DocumentedRuleDefault(
        name="find_zone_transfer_requests",
        check_str=base.RULE_ANY,
        description="List Zone Transfer Requests",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests',
                'method': 'GET'
            }
        ],
    ),
    policy.DocumentedRuleDefault(
        name="update_zone_transfer_request",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Update a Zone Transfer Request",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_request_id}',  # noqa
                'method': 'PATCH'
            }
        ],
        deprecated_rule=deprecated_update_zone_transfer_request
    ),
    policy.DocumentedRuleDefault(
        name="delete_zone_transfer_request",
        check_str=base.SYSTEM_ADMIN_OR_PROJECT_MEMBER,
        scope_types=[constants.PROJECT],
        description="Delete a Zone Transfer Request",
        operations=[
            {
                'path': '/v2/zones/tasks/transfer_requests/{zone_transfer_request_id}',  # noqa
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_delete_zone_transfer_request
    )
]


def list_rules():
    return rules
