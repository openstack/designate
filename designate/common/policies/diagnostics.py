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

from designate.common.policies import base


deprecated_diagnostics_ping = policy.DeprecatedRule(
    name="diagnostics_ping",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_diagnostics_sync_zones = policy.DeprecatedRule(
    name="diagnostics_sync_zones",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_diagnostics_sync_zone = policy.DeprecatedRule(
    name="diagnostics_sync_zone",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_diagnostics_sync_record = policy.DeprecatedRule(
    name="diagnostics_sync_record",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

rules = [
    policy.RuleDefault(
        name="diagnostics_ping",
        check_str=base.SYSTEM_ADMIN,
        scope_types=['system'],
        description='Diagnose ping.',
        deprecated_rule=deprecated_diagnostics_ping),
    policy.RuleDefault(
        name="diagnostics_sync_zones",
        check_str=base.SYSTEM_ADMIN,
        scope_types=['system'],
        description='Diagnose sync zones.',
        deprecated_rule=deprecated_diagnostics_sync_zones),
    policy.RuleDefault(
        name="diagnostics_sync_zone",
        check_str=base.SYSTEM_ADMIN,
        scope_types=['system'],
        description='Diagnose sync zone.',
        deprecated_rule=deprecated_diagnostics_sync_zone),
    policy.RuleDefault(
        name="diagnostics_sync_record",
        check_str=base.SYSTEM_ADMIN,
        scope_types=['system'],
        description='Diagnose sync record.',
        deprecated_rule=deprecated_diagnostics_sync_record)
]


def list_rules():
    return rules
