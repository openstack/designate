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
from designate.objects.base import DesignateObject  # noqa
from designate.objects.base import ListObjectMixin  # noqa
from designate.objects.base import DictObjectMixin  # noqa
from designate.objects.base import PagedListObjectMixin  # noqa
from designate.objects.blacklist import Blacklist, BlacklistList  # noqa
from designate.objects.zone import Zone, ZoneList  # noqa
from designate.objects.zone_attribute import ZoneAttribute, ZoneAttributeList  # noqa
from designate.objects.zone_master import ZoneMaster, ZoneMasterList  # noqa
from designate.objects.floating_ip import FloatingIP, FloatingIPList  # noqa
from designate.objects.pool import Pool, PoolList  # noqa
from designate.objects.pool_also_notify import PoolAlsoNotify, PoolAlsoNotifyList  # noqa
from designate.objects.pool_attribute import PoolAttribute, PoolAttributeList  # noqa
from designate.objects.pool_catalog_zone import PoolCatalogZone  # noqa
from designate.objects.pool_ns_record import PoolNsRecord, PoolNsRecordList  # noqa
from designate.objects.pool_nameserver import PoolNameserver, PoolNameserverList  # noqa
from designate.objects.pool_target import PoolTarget, PoolTargetList  # noqa
from designate.objects.pool_target_master import PoolTargetMaster, PoolTargetMasterList  # noqa
from designate.objects.pool_target_option import PoolTargetOption, PoolTargetOptionList  # noqa
from designate.objects.quota import Quota, QuotaList  # noqa
from designate.objects.record import Record, RecordList  # noqa
from designate.objects.recordset import RecordSet, RecordSetList  # noqa
from designate.objects.service_status import ServiceStatus, ServiceStatusList  # noqa
from designate.objects.shared_zone import SharedZone, SharedZoneList  # noqa
from designate.objects.tenant import Tenant, TenantList  # noqa
from designate.objects.tld import Tld, TldList  # noqa
from designate.objects.tsigkey import TsigKey, TsigKeyList  # noqa
from designate.objects.validation_error import ValidationError  # noqa
from designate.objects.validation_error import ValidationErrorList  # noqa
from designate.objects.zone_transfer_request import ZoneTransferRequest, ZoneTransferRequestList  # noqa
from designate.objects.zone_transfer_accept import ZoneTransferAccept, ZoneTransferAcceptList  # noqa
from designate.objects.zone_import import ZoneImport, ZoneImportList  # noqa
from designate.objects.zone_export import ZoneExport, ZoneExportList  # noqa

#  Record Types

from designate.objects.rrdata_a import A, AList  # noqa
from designate.objects.rrdata_aaaa import AAAA, AAAAList  # noqa
from designate.objects.rrdata_caa import CAA, CAAList  # noqa
from designate.objects.rrdata_cert import CERT, CERTList  # noqa
from designate.objects.rrdata_cname import CNAME, CNAMEList  # noqa
from designate.objects.rrdata_mx import MX, MXList  # noqa
from designate.objects.rrdata_naptr import NAPTR, NAPTRList  # noqa
from designate.objects.rrdata_ns import NS, NSList  # noqa
from designate.objects.rrdata_ptr import PTR, PTRList  # noqa
from designate.objects.rrdata_soa import SOA, SOAList  # noqa
from designate.objects.rrdata_spf import SPF, SPFList  # noqa
from designate.objects.rrdata_srv import SRV, SRVList  # noqa
from designate.objects.rrdata_sshfp import SSHFP, SSHFPList  # noqa
from designate.objects.rrdata_txt import TXT, TXTList  # noqa
