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


deprecated_all_tenants = policy.DeprecatedRule(
    name="all_tenants",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_edit_managed_records = policy.DeprecatedRule(
    name="edit_managed_records",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_use_low_ttl = policy.DeprecatedRule(
    name="use_low_ttl",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_use_sudo = policy.DeprecatedRule(
    name="use_sudo",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)
deprecated_hard_delete = policy.DeprecatedRule(
    name="hard_delete",
    check_str=base.RULE_ADMIN,
    deprecated_reason=base.DEPRECATED_REASON,
    deprecated_since=versionutils.deprecated.WALLABY
)

rules = [
    policy.RuleDefault(
        name="all_tenants",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Action on all tenants.',
        deprecated_rule=deprecated_all_tenants),
    policy.RuleDefault(
        name="edit_managed_records",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Edit managed records.',
        deprecated_rule=deprecated_edit_managed_records),
    policy.RuleDefault(
        name="use_low_ttl",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Use low TTL.',
        deprecated_rule=deprecated_use_low_ttl),
    policy.RuleDefault(
        name="use_sudo",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description='Accept sudo from user to tenant.',
        deprecated_rule=deprecated_use_sudo),
    policy.RuleDefault(
        name="hard_delete",
        check_str=base.SYSTEM_ADMIN,
        scope_types=[constants.PROJECT],
        description="Clean backend resources associated with zone",
        deprecated_rule=deprecated_hard_delete),
]


def list_rules():
    return rules
