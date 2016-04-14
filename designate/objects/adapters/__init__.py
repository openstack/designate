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
# Base Adapter Class
from designate.objects.adapters.base import DesignateAdapter  # noqa
# API v2
from designate.objects.adapters.api_v2.blacklist import BlacklistAPIv2Adapter, BlacklistListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.zone import ZoneAPIv2Adapter, ZoneListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.zone_attribute import ZoneAttributeAPIv2Adapter, ZoneAttributeListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.zone_master import ZoneMasterAPIv2Adapter, ZoneMasterListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.floating_ip import FloatingIPAPIv2Adapter, FloatingIPListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.record import RecordAPIv2Adapter, RecordListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.recordset import RecordSetAPIv2Adapter, RecordSetListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.pool import PoolAPIv2Adapter, PoolListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.pool_attribute import PoolAttributeAPIv2Adapter, PoolAttributeListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.pool_ns_record import PoolNsRecordAPIv2Adapter, PoolNsRecordListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.tld import TldAPIv2Adapter, TldListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.tsigkey import TsigKeyAPIv2Adapter, TsigKeyListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.quota import QuotaAPIv2Adapter, QuotaListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.service_status import ServiceStatusAPIv2Adapter, ServiceStatusListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.zone_transfer_accept import ZoneTransferAcceptAPIv2Adapter, ZoneTransferAcceptListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.zone_transfer_request import ZoneTransferRequestAPIv2Adapter, ZoneTransferRequestListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.validation_error import ValidationErrorAPIv2Adapter, ValidationErrorListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.zone_import import ZoneImportAPIv2Adapter, ZoneImportListAPIv2Adapter  # noqa
from designate.objects.adapters.api_v2.zone_export import ZoneExportAPIv2Adapter, ZoneExportListAPIv2Adapter  # noqa

# YAML

from designate.objects.adapters.yaml.pool import PoolYAMLAdapter, PoolListYAMLAdapter  # noqa
from designate.objects.adapters.yaml.pool_attribute import PoolAttributeYAMLAdapter, PoolAttributeListYAMLAdapter  # noqa
from designate.objects.adapters.yaml.pool_also_notify import PoolAlsoNotifyYAMLAdapter, PoolAlsoNotifyListYAMLAdapter  # noqa
from designate.objects.adapters.yaml.pool_nameserver import PoolNameserverYAMLAdapter, PoolNameserverListYAMLAdapter  # noqa
from designate.objects.adapters.yaml.pool_ns_record import PoolNsRecordYAMLAdapter, PoolNsRecordListYAMLAdapter  # noqa
from designate.objects.adapters.yaml.pool_target import PoolTargetYAMLAdapter, PoolTargetListYAMLAdapter  # noqa
from designate.objects.adapters.yaml.pool_target_master import PoolTargetMasterYAMLAdapter, PoolTargetMasterListYAMLAdapter  # noqa
from designate.objects.adapters.yaml.pool_target_option import PoolTargetOptionYAMLAdapter, PoolTargetOptionListYAMLAdapter  # noqa
