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
        name="create_recordset",
        check_str=base.RULE_ZONE_PRIMARY_OR_ADMIN,
        description="Create Recordset",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets',
                'method': 'POST'
            }, {
                'path': '/v2/reverse/floatingips/{region}:{floatingip_id}',
                'method': 'PATCH'
            }
        ]
    ),
    policy.RuleDefault(
        name="get_recordsets",
        check_str=base.RULE_ADMIN_OR_OWNER
    ),
    policy.DocumentedRuleDefault(
        name="get_recordset",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Get recordset",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'GET'
            }, {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'DELETE'
            }, {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'PUT'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="update_recordset",
        check_str=base.RULE_ZONE_PRIMARY_OR_ADMIN,
        description="Update recordset",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'PUT'
            }, {
                'path': '/v2/reverse/floatingips/{region}:{floatingip_id}',
                'method': 'PATCH'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="delete_recordset",
        check_str=base.RULE_ZONE_PRIMARY_OR_ADMIN,
        description="Delete RecordSet",
        operations=[
            {
                'path': '/v2/zones/{zone_id}/recordsets/{recordset_id}',
                'method': 'DELETE'
            }
        ]
    ),
    policy.RuleDefault(
        name="count_recordset",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description="Count recordsets"
    )
]


def list_rules():
    return rules
