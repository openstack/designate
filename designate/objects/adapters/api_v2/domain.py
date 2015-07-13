# Copyright 2014 Hewlett-Packard Development Company, L.P.
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
from oslo_log import log as logging

from designate.objects.adapters.api_v2 import base
from designate import objects
from designate import exceptions

LOG = logging.getLogger(__name__)


class DomainAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.Domain

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "pool_id": {},
            "project_id": {
                'rename': 'tenant_id'
            },
            "name": {
                'immutable': True,
            },
            "email": {
                'read_only': False
            },
            "description": {
                'read_only': False
            },
            "ttl": {
                'read_only': False
            },
            "serial": {},
            "status": {},
            "action": {},
            "version": {},
            "type": {
                'immutable': True
            },
            "masters": {},
            "created_at": {},
            "updated_at": {},
            "transferred_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'zone',
            'collection_name': 'zones',
        }
    }

    @classmethod
    def _parse_object(cls, values, object, *args, **kwargs):
        # TODO(Graham): Remove this when
        # https://bugs.launchpad.net/designate/+bug/1432842 is fixed

        if 'masters' in values:
            if isinstance(values['masters'], list):
                object.set_masters(values.get('masters'))
                del values['masters']
            else:
                errors = objects.ValidationErrorList()
                e = objects.ValidationError()
                e.path = ['masters']
                e.validator = 'type'
                e.validator_value = ["list"]
                e.message = ("'%(data)s' is not a valid list of masters"
                             % {'data': values['masters']})
                # Add it to the list for later
                errors.append(e)
                raise exceptions.InvalidObject(
                    "Provided object does not match "
                    "schema", errors=errors, object=cls.ADAPTER_OBJECT())

        return super(DomainAPIv2Adapter, cls)._parse_object(
            values, object, *args, **kwargs)


class DomainListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.DomainList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'zone',
            'collection_name': 'zones',
        }
    }
