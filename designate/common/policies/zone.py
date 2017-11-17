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
    policy.DocumentedRuleDefault(
        name="create_zone",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Create Zone",
        operations=[
            {
                'path': '/v2/zones',
                'method': 'POST'
            }
        ]
    ),
    policy.RuleDefault(
        name="get_zones",
        check_str=base.RULE_ADMIN_OR_OWNER
    ),
    policy.DocumentedRuleDefault(
        name="get_zone",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Get Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}',
                'method': 'GET'
            }, {
                'path': '/v2/zones/{zone_id}',
                'method': 'PATCH'
            }, {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'PUT'
            }
        ]
    ),
    policy.RuleDefault(
        name="get_zone_servers",
        check_str=base.RULE_ADMIN_OR_OWNER
    ),
    policy.DocumentedRuleDefault(
        name="find_zones",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="List existing zones",
        operations=[
            {
                'path': '/v2/zones',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="update_zone",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Update Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}',
                'method': 'PATCH'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="delete_zone",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Delete Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="xfr_zone",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Manually Trigger an Update of a Secondary Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/xfr',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="abandon_zone",
        check_str=base.RULE_ADMIN,
        description="Abandon Zone",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/tasks/abandon',
                'method': 'POST'
            }
        ]
    ),
    policy.RuleDefault(
        name="count_zones",
        check_str=base.RULE_ADMIN_OR_OWNER
    ),
    policy.RuleDefault(
        name="count_zones_pending_notify",
        check_str=base.RULE_ADMIN_OR_OWNER
    ),
    policy.RuleDefault(
        name="purge_zones",
        check_str=base.RULE_ADMIN
    ),
    policy.RuleDefault(
        name="touch_zone",
        check_str=base.RULE_ADMIN_OR_OWNER
    )
]


def list_rules():
    return rules
