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
LOG = logging.getLogger(__name__)


class QuotaAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.Quota

    MODIFICATIONS = {
        'fields': {
            'zones': {
                'rename': 'domains',
                'read_only': False
            },
            'zone_records': {
                'rename': 'domain_records',
                'read_only': False
            },
            'zone_recordsets': {
                'rename': 'domain_recordsets',
                'read_only': False
            },
            'recordset_records': {
                'read_only': False
            },

        },
        'options': {
            'links': True,
            'resource_name': 'quota',
            'collection_name': 'quotas',
        }
    }


class QuotaListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.QuotaList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'quota',
            'collection_name': 'quotas',
        }
    }
