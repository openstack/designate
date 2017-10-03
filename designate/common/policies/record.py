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
        name="create_record",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Create record.',
        operations=[
            {
                'path': '/v1/domains/<uuid:domain_id>/records',
                'method': 'POST'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_records",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Get records.',
        operations=[
            {
                'path': '/v1/domains/<uuid:domain_id>/records',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="get_record",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Get record.',
        operations=[
            {
                'path': '/v1/domains/<uuid:domain_id>/records/<uuid:record_id>',  # noqa
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_records",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Find records.',
        operations=[
            {
                'path': '/v2/reverse/floatingips/{region}:{floatingip_id}',
                'method': 'GET'
            }, {
                'path': '/v2/reverse/floatingips',
                'method': 'GET'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="find_record",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Find record.',
        operations=[
            {
                'path': '/v1/domains/<uuid:domain_id>/records/<uuid:record_id>',  # noqa
                'method': 'GET'
            }, {
                'path': '/v1/domains/<uuid:domain_id>/records/<uuid:record_id>',  # noqa
                'method': 'DELETE'
            }, {
                'path': '/v1/domains/<uuid:domain_id>/records/<uuid:record_id>',  # noqa
                'method': 'PUT'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="update_record",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Update record.',
        operations=[
            {
                'path': '/v1/domains/<uuid:domain_id>/records/<uuid:record_id>',  # noqa
                'method': 'PUT'
            }
        ]
    ),
    policy.DocumentedRuleDefault(
        name="delete_record",
        check_str=base.RULE_ADMIN_OR_OWNER,
        description='Delete record.',
        operations=[
            {
                'path': '/v1/domains/<uuid:domain_id>/records/<uuid:record_id>',  # noqa
                'method': 'DELETE'
            }
        ]
    ),
    policy.RuleDefault(
        name="count_records",
        check_str=base.RULE_ADMIN_OR_OWNER)
]


def list_rules():
    return rules
