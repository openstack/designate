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

from designate.common.policies import base


rules = [
    policy.RuleDefault(
        name="all_tenants",
        check_str=base.RULE_ADMIN,
        description='Action on all tenants.'),
    policy.RuleDefault(
        name="edit_managed_records",
        check_str=base.RULE_ADMIN,
        description='Edit managed records.'),
    policy.RuleDefault(
        name="use_low_ttl",
        check_str=base.RULE_ADMIN,
        description='Use low TTL.'),
    policy.RuleDefault(
        name="use_sudo",
        check_str=base.RULE_ADMIN,
        description='Accept sudo from user to tenant.')
]


def list_rules():
    return rules
