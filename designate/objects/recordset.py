# Copyright (c) 2014 Rackspace Hosting
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
from designate.objects import base


class RecordSet(base.DictObjectMixin, base.PersistentObjectMixin,
                base.DesignateObject):
    @property
    def action(self):
        # Return action as UPDATE if present. CREATE and DELETE are returned
        # if they are the only ones.
        action = 'NONE'
        actions = {'CREATE': 0, 'DELETE': 0, 'UPDATE': 0, 'NONE': 0}
        for record in self.records:
            actions[record.action] += 1

        if actions['CREATE'] != 0 and actions['UPDATE'] == 0 and \
                actions['DELETE'] == 0 and actions['NONE'] == 0:
            action = 'CREATE'
        elif actions['DELETE'] != 0 and actions['UPDATE'] == 0 and \
                actions['CREATE'] == 0 and actions['NONE'] == 0:
            action = 'DELETE'
        elif actions['UPDATE'] != 0 or actions['CREATE'] != 0 or \
                actions['DELETE'] != 0:
            action = 'UPDATE'
        return action

    @property
    def status(self):
        # Return the worst status in order of ERROR, PENDING, ACTIVE
        status = 'ACTIVE'
        for record in self.records:
            if (record.status == 'ERROR') or \
                    (record.status == 'PENDING' and status != 'ERROR') or \
                    (status != 'PENDING'):
                status = record.status
        return status

    FIELDS = {
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
            'required': True,
            'read_only': True
        },
        'domain_id': {
            'schema': {
                'type': 'string',
                'description': 'Zone identifier',
                'format': 'uuid'
            },
            'read_only': True,
            'required': True
        },
        'name': {
            'schema': {
                'type': 'string',
                'description': 'Zone name',
                'format': 'domainname',
                'maxLength': 255,
            },
            'immutable': True,
            'required': True
        },
        'type': {
            'schema': {
                'type': 'string',
                'description': 'RecordSet type (TODO: Make types extensible)',
                'enum': ['A', 'AAAA', 'CNAME', 'MX', 'SRV', 'TXT', 'SPF', 'NS',
                         'PTR', 'SSHFP', 'SOA']
            },
            'required': True,
            'immutable': True
        },
        'ttl': {
            'schema': {
                'type': 'integer',
                'description': 'Default time to live',
                'minimum': 0,
                'maximum': 2147483647
            },
        },
        'description': {
            'schema': {
                'type': ['string', 'null'],
                'maxLength': 160
            },
        },
        'records': {
            'relation': True,
            'relation_cls': 'RecordList'
        },
    }


class RecordSetList(base.ListObjectMixin, base.DesignateObject,
                    base.PagedListObjectMixin):
    LIST_ITEM_TYPE = RecordSet
