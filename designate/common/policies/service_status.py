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
The service status API now supports system scope and default roles.
"""

deprecated_find_service_status = policy.DeprecatedRule(
    name="find_service_status",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_find_service_statuses = policy.DeprecatedRule(
    name="find_service_statuses",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_update_service_status = policy.DeprecatedRule(
    "update_service_status",
    base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_delete_service_status = policy.DeprecatedRule(
    "delete_service_status",
    base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="find_service_status",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description="Find a single Service Status",
        operations=[
            {
                'path': '/v2/service_status/{service_id}',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_service_status
    ),
    policy.DocumentedRuleDefault(
        name="find_service_statuses",
        check_str=base.SYSTEM_READER,
        scope_types=[constants.PROJECT],
        description="List service statuses.",
        operations=[
            {
                'path': '/v2/service_status',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_service_statuses
    ),
    policy.RuleDefault(
        name="update_service_status",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_update_service_status
    ),
    policy.RuleDefault(
        name="delete_service_status",
        check_str=base.SYSTEM_ADMIN,
        scope_types=['system'],
        deprecated_rule=deprecated_delete_service_status
    )
]


def list_rules():
    return rules
