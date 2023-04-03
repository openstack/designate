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
The quota API now supports system scope and default roles.
"""

deprecated_get_quotas = policy.DeprecatedRule(
    name="get_quotas",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_set_quota = policy.DeprecatedRule(
    name="set_quota",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_reset_quotas = policy.DeprecatedRule(
    name="reset_quotas",
    check_str=base.RULE_ADMIN,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

rules = [
    policy.DocumentedRuleDefault(
        name="get_quotas",
        check_str=base.SYSTEM_OR_PROJECT_READER_OR_ALL_TENANTS_READER,
        scope_types=[constants.PROJECT],
        description="View Current Project's Quotas.",
        operations=[
            {
                'path': '/v2/quotas',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_get_quotas
    ),
    policy.DocumentedRuleDefault(
        name="set_quota",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Set Quotas.',
        operations=[
            {
                'path': '/v2/quotas/{project_id}',
                'method': 'PATCH'
            }
        ],
        deprecated_rule=deprecated_set_quota
    ),
    policy.DocumentedRuleDefault(
        name="reset_quotas",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Reset Quotas.',
        operations=[
            {
                'path': '/v2/quotas/{project_id}',
                'method': 'DELETE'
            }
        ],
        deprecated_rule=deprecated_reset_quotas
    ),
]


def list_rules():
    return rules
