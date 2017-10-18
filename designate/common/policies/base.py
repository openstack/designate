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


from oslo_policy import policy


RULE_ADMIN_OR_OWNER = 'rule:admin_or_owner'
RULE_ADMIN = 'rule:admin'
RULE_ZONE_PRIMARY_OR_ADMIN = \
    "('PRIMARY':%(zone_type)s and rule:admin_or_owner) "\
    "OR ('SECONDARY':%(zone_type)s AND is_admin:True)"
RULE_ZONE_TRANSFER = "rule:admin_or_owner OR tenant:%(target_tenant_id)s " \
                     "OR None:%(target_tenant_id)s"
RULE_ANY = "@"

rules = [
    policy.RuleDefault(
        name="admin",
        check_str="role:admin or is_admin:True"),
    policy.RuleDefault(
        name="primary_zone",
        check_str="target.zone_type:SECONDARY"),
    policy.RuleDefault(
        name="owner",
        check_str="tenant:%(tenant_id)s"),
    policy.RuleDefault(
        name="admin_or_owner",
        check_str="rule:admin or rule:owner"),
    policy.RuleDefault(
        name="default",
        check_str="rule:admin_or_owner"),
    policy.RuleDefault(
        name="target",
        check_str="tenant:%(target_tenant_id)s"),
    policy.RuleDefault(
        name="owner_or_target",
        check_str="rule:target or rule:owner"),
    policy.RuleDefault(
        name="admin_or_owner_or_target",
        check_str="rule:owner_or_target or rule:admin"),
    policy.RuleDefault(
        name="admin_or_target",
        check_str="rule:admin or rule:target"),
    policy.RuleDefault(
        name="zone_primary_or_admin",
        check_str=RULE_ZONE_PRIMARY_OR_ADMIN)
]


def list_rules():
    return rules
