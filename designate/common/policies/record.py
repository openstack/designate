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
The records API now supports system scope and default roles.
"""

deprecated_find_records = policy.DeprecatedRule(
    name="find_records",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_count_records = policy.DeprecatedRule(
    name="count_records",
    check_str=base.RULE_ADMIN_OR_OWNER,
    deprecated_reason=DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)


rules = [
    policy.DocumentedRuleDefault(
        name="find_records",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        description='Find records.',
        operations=[
            {
                'path': '/v2/reverse/floatingips/{region}:{floatingip_id}',
                'method': 'GET'
            }, {
                'path': '/v2/reverse/floatingips',
                'method': 'GET'
            }
        ],
        deprecated_rule=deprecated_find_records
    ),
    policy.RuleDefault(
        name="count_records",
        check_str=base.SYSTEM_OR_PROJECT_READER,
        scope_types=[constants.PROJECT],
        deprecated_rule=deprecated_count_records
    )
]


def list_rules():
    return rules
