# Copyright 2021 Red Hat
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

# API constants
API_REF_URL = 'https://docs.openstack.org/api-ref/dns'
CURRENT = 'CURRENT'
SUPPORTED = 'SUPPORTED'
DEPRECATED = 'DEPRECATED'
EXPERIMENTAL = 'EXPERIMENTAL'

# RBAC related constants
RBAC_PROJECT_ID = 'project_id'
RBAC_TARGET_PROJECT_ID = 'target_project_id'

# Statuses
ACTIVE = 'ACTIVE'
ERROR = 'ERROR'
INACTIVE = 'INACTIVE'
PENDING = 'PENDING'

# Actions
CREATE = 'CREATE'
DELETE = 'DELETE'
NONE = 'NONE'
UPDATE = 'UPDATE'

# Floating IP constants
FLOATING_IP_ACTIONS = [CREATE, DELETE, UPDATE, NONE]
FLOATING_IP_STATUSES = [ACTIVE, ERROR, INACTIVE, PENDING]

# Quotas
MIN_QUOTA = -1
MAX_QUOTA = 2147483647
QUOTA_API_EXPORT_SIZE = 'api_export_size'
QUOTA_RECORDSET_RECORDS = 'recordset_records'
QUOTA_ZONE_RECORDS = 'zone_records'
QUOTA_ZONE_RECORDSETS = 'zone_recordsets'
QUOTA_ZONES = 'zones'
VALID_QUOTAS = [QUOTA_API_EXPORT_SIZE, QUOTA_RECORDSET_RECORDS,
                QUOTA_ZONE_RECORDS, QUOTA_ZONE_RECORDSETS, QUOTA_ZONES]
