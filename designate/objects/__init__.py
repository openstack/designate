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
from designate.objects.base import DictObjectMixin  # noqa
from designate.objects.base import ListObjectMixin  # noqa
from designate.objects.base import PagedListObjectMixin  # noqa
from designate.objects.backend_option import BackendOption, BackendOptionList  # noqa
from designate.objects.blacklist import Blacklist, BlacklistList  # noqa
from designate.objects.domain import Domain, DomainList  # noqa
from designate.objects.pool_manager_status import PoolManagerStatus, PoolManagerStatusList  # noqa
from designate.objects.pool_server import PoolServer, PoolServerList  # noqa
from designate.objects.pool import Pool, PoolList  # noqa
from designate.objects.poolattribute import PoolAttribute  # noqa
from designate.objects.poolattribute import PoolAttributeList  # noqa
from designate.objects.nameserver import NameServer, NameServerList  # noqa
from designate.objects.quota import Quota, QuotaList  # noqa
from designate.objects.rrdata_a import RRData_A  # noqa
from designate.objects.rrdata_aaaa import RRData_AAAA  # noqa
from designate.objects.rrdata_cname import RRData_CNAME  # noqa
from designate.objects.rrdata_mx import RRData_MX  # noqa
from designate.objects.rrdata_ns import RRData_NS  # noqa
from designate.objects.rrdata_ptr import RRData_PTR  # noqa
from designate.objects.rrdata_soa import RRData_SOA  # noqa
from designate.objects.rrdata_spf import RRData_SPF  # noqa
from designate.objects.rrdata_srv import RRData_SRV  # noqa
from designate.objects.rrdata_sshfp import RRData_SSHFP  # noqa
from designate.objects.rrdata_txt import RRData_TXT  # noqa
from designate.objects.record import Record, RecordList  # noqa
from designate.objects.recordset import RecordSet, RecordSetList  # noqa
from designate.objects.server import Server, ServerList  # noqa
from designate.objects.tenant import Tenant, TenantList  # noqa
from designate.objects.tld import Tld, TldList  # noqa
from designate.objects.tsigkey import TsigKey, TsigKeyList  # noqa
from designate.objects.validation_error import ValidationError  # noqa
from designate.objects.validation_error import ValidationErrorList  # noqa
from designate.objects.zone_transfer_request import ZoneTransferRequest, ZoneTransferRequestList  # noqa
from designate.objects.zone_transfer_accept import ZoneTransferAccept, ZoneTransferAcceptList  # noqa
